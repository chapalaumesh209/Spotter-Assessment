import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from fuel_optimizer.models import FuelStation
from fuel_optimizer.services.fuel_stations import FuelStationService

class Command(BaseCommand):
    help = "Loads and validates fuel station data into the Django database and in-memory spatial cache."

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            default=settings.PROCESSED_DATA_PATH,
            help='Path to the processed fuel CSV file'
        )

    def handle(self, *args, **options):
        csv_path = options['csv_path']
        if not os.path.exists(csv_path):
            self.stderr.write(self.style.ERROR(f"File not found: {csv_path}"))
            return

        self.stdout.write(f"Loading fuel stations from {csv_path}...")
        df = pd.read_csv(csv_path)

        # Clear existing
        FuelStation.objects.all().delete()

        stations_to_create = []
        for _, row in df.iterrows():
            if pd.isna(row.get('latitude')) or pd.isna(row.get('longitude')):
                continue
            stations_to_create.append(FuelStation(
                opis_id=int(row['OPIS Truckstop ID']),
                name=str(row['Truckstop Name']),
                address=str(row['Address']),
                city=str(row['City']),
                state=str(row['State']),
                rack_id=int(row.get('Rack ID', 0)),
                retail_price=float(row['Retail Price']),
                latitude=float(row['latitude']),
                longitude=float(row['longitude'])
            ))

        FuelStation.objects.bulk_create(stations_to_create, batch_size=1000)
        
        # Warm in-memory service
        FuelStationService.get_instance().load_stations(csv_path)

        self.stdout.write(self.style.SUCCESS(
            f"Successfully imported {len(stations_to_create)} fuel stations into database and cache."
        ))

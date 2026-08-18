from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

class RouteAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_check_endpoint(self):
        response = self.client.get('/api/v1/health')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "healthy")

    def test_root_endpoint(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

    def test_validation_error_missing_finish(self):
        response = self.client.post('/api/v1/route', {"start": "New York, NY"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_validation_error_empty_strings(self):
        response = self.client.post('/api/v1/route', {"start": "", "finish": ""}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("fuel_optimizer.views.GeocodingService.geocode")
    @patch("fuel_optimizer.views.RoutingService.get_route")
    def test_successful_route_api(self, mock_get_route, mock_geocode):
        mock_geocode.side_effect = [
            (40.7128, -74.0060),  # New York
            (39.9526, -75.1652)   # Philadelphia
        ]
        mock_get_route.return_value = {
            "distance_miles": 95.0,
            "duration_minutes": 110.0,
            "geometry": {
                "type": "LineString",
                "coordinates": [[-74.0060, 40.7128], [-75.1652, 39.9526]]
            }
        }

        response = self.client.post(
            '/api/v1/route',
            {"start": "New York, NY", "finish": "Philadelphia, PA"},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["start"]["address"], "New York, NY")
        self.assertEqual(data["finish"]["address"], "Philadelphia, PA")
        self.assertEqual(data["vehicle"]["max_range_miles"], 500.0)
        self.assertEqual(data["vehicle"]["mpg"], 10.0)
        self.assertEqual(data["route"]["distance_miles"], 95.0)
        self.assertEqual(data["fuel"]["total_fuel_consumed"], 9.5)
        self.assertEqual(len(data["fuel_stops"]), 0)

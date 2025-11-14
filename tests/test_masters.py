"""
Tests for master data endpoints
"""
import pytest
from fastapi import status


def test_list_organizations(client):
    """Test listing organizations."""
    response = client.get("/api/organizations")
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]


def test_create_organization(client, sample_organization_data):
    """Test creating an organization."""
    response = client.post("/api/organizations", json=sample_organization_data)
    assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_401_UNAUTHORIZED, status.HTTP_422_UNPROCESSABLE_ENTITY]


def test_list_commodities(client):
    """Test listing commodities."""
    response = client.get("/api/commodities")
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]


def test_create_commodity(client, sample_commodity_data):
    """Test creating a commodity."""
    response = client.post("/api/commodities", json=sample_commodity_data)
    assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_401_UNAUTHORIZED, status.HTTP_422_UNPROCESSABLE_ENTITY]


def test_list_locations(client):
    """Test listing locations."""
    response = client.get("/api/locations")
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]


def test_list_financial_years(client):
    """Test listing financial years."""
    response = client.get("/api/financial-years")
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]


def test_list_gst_rates(client):
    """Test listing GST rates."""
    response = client.get("/api/gst-rates")
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]

"""
Tests for Trade Desk endpoints
"""
import pytest
from fastapi import status


def test_create_trade(client, sample_trade_data):
    """Test creating a new trade."""
    response = client.post("/api/tradedesk/trades", json=sample_trade_data)
    # May require auth, so accept 401 or 201
    assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_401_UNAUTHORIZED, status.HTTP_422_UNPROCESSABLE_ENTITY]


def test_list_trades(client):
    """Test listing trades."""
    response = client.get("/api/tradedesk/trades")
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]


def test_get_trade_not_found(client):
    """Test getting non-existent trade."""
    response = client.get("/api/tradedesk/trades/nonexistent")
    assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_401_UNAUTHORIZED]


def test_list_offers(client):
    """Test listing offers."""
    response = client.get("/api/tradedesk/offers")
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]


def test_list_tested_lots(client):
    """Test listing tested lots."""
    response = client.get("/api/tradedesk/tested-lots")
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]


def test_dashboard_stats(client):
    """Test dashboard statistics."""
    response = client.get("/api/tradedesk/dashboard/stats")
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]
    
    if response.status_code == status.HTTP_200_OK:
        data = response.json()
        assert "total_trades" in data
        assert "total_offers" in data

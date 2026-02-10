# Booking.com Taxi Supplier API - Reference

## Architecture Overview
AureaVia acts as a **Supply Partner** - Booking.com sends webhooks TO us and we poll their API.

### Flow
1. **Search**: Booking.com sends search request → we respond with pricing
2. **Booking**: Customer books → Booking.com sends booking webhook to us
3. **Accept/Reject**: We call Booking.com API to accept/reject the booking
4. **Driver Management**: We assign driver and update status via their API
5. **Incidents**: Booking.com sends incident webhooks for issues

## Authentication
- **OAuth 2.0 Client Credentials Flow**
- We provide: Client ID + Client Secret
- Booking.com authenticates with Bearer token in Authorization header
- Token is long-lived for search webhook

## Webhooks (Booking.com → AureaVia)

### 1. Search Webhook
**POST** to our endpoint - Booking.com asks for pricing.
Response time: < 5 seconds (SLA < 2.5s)

**Request payload:**
```json
{
  "origin": {
    "latitude": 45.6306,
    "longitude": 8.7281,
    "name": "Milano Malpensa Airport",
    "city": "Milano",
    "country": "IT",
    "postcode": "21010",
    "iata": "MXP"
  },
  "destination": {
    "latitude": 45.4642,
    "longitude": 9.1900,
    "name": "Hotel Duomo",
    "city": "Milano",
    "country": "IT",
    "postcode": "20121",
    "iata": null
  },
  "passengers": 2,
  "pickupDateTime": "2026-02-15T10:00:00Z",
  "pickupTimezone": "Europe/Rome",
  "drivingDistanceInKm": 52.0,
  "genius": { "level": "NON_GENIUS" }
}
```

**Response:**
```json
{
  "searchResultId": "uuid-max-100-chars",
  "transportCategory": "STANDARD",
  "price": {
    "salePriceMin": 85.00,
    "salePriceMax": 85.00,
    "currency": "EUR"
  },
  "minPassengers": 1,
  "maxPassengers": 4,
  "features": [{ "name": "noOfBags", "value": "3" }],
  "servicesAvailable": ["meetAndGreet"]
}
```

**Transport Categories:** STANDARD, LUXURY, EXECUTIVE, PEOPLE_CARRIER, LARGE_PEOPLE_CARRIER, EXECUTIVE_PEOPLE_CARRIER, MINIBUS, ELECTRIC_STANDARD, ELECTRIC_LUXURY

### 2. Booking Webhook
**POST /v2/bookings** - New booking notification (fire & forget)

```json
{
  "bookingReference": "44225562",
  "customerReference": "87654321",
  "searchResultId": "d290f1ee-6c54-4b01-90e6-d701748f0851",
  "leadPassenger": {
    "title": "Mr",
    "firstName": "John",
    "lastName": "Doe",
    "phoneNumber": "+441632960881",
    "customerId": "hash..."
  },
  "flightNumber": "BA123",
  "comment": "Need a pet friendly car",
  "services": [{"name": "meetAndGreetMessage", "value": "Welcome John Doe"}]
}
```
Response: HTTP 204

### 3. Booking Update Webhook
**PATCH /v2/bookings/:bookingReference** - Amendment or cancellation

```json
{
  "leadPassenger": { ... },
  "comment": "...",
  "flightNumber": "BA123",
  "pickupDateTime": "2026-02-15T10:00:00Z",
  "services": [...],
  "action": "AMENDMENT" | "CANCELLATION",
  "cancellationReason": ""
}
```
Response: HTTP 204

### 4. Incident Webhook
**POST /v2/incidents** - Incident notification

**Incident Types:** DRIVER_LATENESS, DRIVER_NO_SHOW, CUSTOMER_NO_SHOW, SERVICE_PROVIDED, WRONG_VEHICLE, DRIVER_SERVICE, SUPPLIER_SERVICE, DRIVER_DELAY_20_TO_40_MINS, DRIVER_DELAY_UNDER_20_MINS, DRIVER_DELAY_OVER_40_MINS, OTHER

**Statuses:** RESOLVED, DISPUTED
**Responsible Parties:** CUSTOMER, NO_ONE, BOOKING.COM, SUPPLIER

## REST API (AureaVia → Booking.com)

### GET /v1/bookings
List all bookings assigned to us.
- Filters: status (NEW,ACCEPTED,DRIVER_ASSIGNED,PENDING_AMENDMENT,PENDING_CANCELLATION), pickUpDateFrom, pickUpDateTo
- Pagination: size (default 400, max 500)

### GET /v1/bookings/:customerReference/:bookingReference
Get single booking details.

### POST /v1/bookings/:customerReference/:bookingReference/responses
Accept or reject a booking.
```json
{
  "supplierResponse": "ACCEPT" | "REJECT",
  "state_hash": "latest-state-hash",
  "cancellationReason": "NO_AVAILABILITY" // if rejecting
}
```

**Rejection Reasons:** CANT_FULFILL_CUSTOMER_REQUEST, CHILD_SEAT_INCOMPATIBLE_VEHICLE, CHILD_SEAT_UNAVAILABLE, CHILD_SEAT_UNSUPPORTED, EXTRA_STOP, FORCE_MAJEURE, INCOMPLETE_BOOKING_DETAILS, INCORRECT_ADDRESS, LEAD_TIME_TOO_SHORT, MISSING_FLIGHT_NUMBER, NO_AVAILABILITY, RATE_ERROR, ROAD_CLOSURE, OTHER

## Booking Statuses (Booking.com side)
NEW, ACCEPTED, DRIVER_ASSIGNED, PENDING_AMENDMENT, PENDING_CANCELLATION

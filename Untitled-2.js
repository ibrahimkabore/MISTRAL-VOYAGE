{
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc0NDI4NDk0OSwiaWF0IjoxNzQ0MTk4NTQ5LCJqdGkiOiIzY2Y3YTk1NTk1ZDQ0ZTVhOGIyNmM3NjAzYTc2MDMyNSIsInVzZXJfaWQiOiI0MWU5YzQxOS05OTJkLTQ3NTUtYTUzMi1iNWQzZTQ0ZDgzNWMifQ.9YGZ7SOqk-rmb2khbRPLoF3OzJvF1LgYTXkyuYyZDgM",
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQ0MjAyMTQ5LCJpYXQiOjE3NDQxOTg1NDksImp0aSI6ImVlNGJlZTZiNjRlNzQ1Mjk4MmM2YWExMGVmNWQ1ZGZhIiwidXNlcl9pZCI6IjQxZTljNDE5LTk5MmQtNDc1NS1hNTMyLWI1ZDNlNDRkODM1YyJ9.TtstBLn_iedRW4fJOSimfZN8nYIf4ELwwsT9XMVUjuA",
    "user": {
        "id": "41e9c419-992d-4755-a532-b5d3e44d835c",
        "username": "Kabore20",
        "email": "kaboremessi@gmail.com",
        "first_name": "Kabore",
        "last_name": "Messi",
        "phone": "1234567890",
        "gender": "H",
        "photos": null,
        "currency": "",
        "pays": "",
        "ville": ""
    }
}




{
    "origin": {
        "code": "ABJ",
        "name": "Aéroport ABJ"
    },
    "destination": {
        "code": "CDG",
        "name": "CHARLES DE GAULLE",
        "city": "PARIS",
        "country": "FRANCE"
    },
    "flight_offers": [
        {
            "type": "flight-offer",
            "id": "1",
            "source": "GDS",
            "instantTicketingRequired": false,
            "nonHomogeneous": false,
            "oneWay": false,
            "isUpsellOffer": false,
            "lastTicketingDate": "2025-04-15",
            "lastTicketingDateTime": "2025-04-15",
            "numberOfBookableSeats": 5,
            "itineraries": [
                {
                    "duration": "PT9H30M",
                    "segments": [
                        {
                            "departure": {
                                "iataCode": "ABJ",
                                "at": "2025-05-15T20:00:00"
                            },
                            "arrival": {
                                "iataCode": "BRU",
                                "at": "2025-05-16T05:00:00"
                            },
                            "carrierCode": "SN",
                            "number": "329",
                            "aircraft": {
                                "code": "333"
                            },
                            "operating": {
                                "carrierCode": "SN"
                            },
                            "duration": "PT7H",
                            "id": "16",
                            "numberOfStops": 0,
                            "blacklistedInEU": false
                        },
                        {
                            "departure": {
                                "iataCode": "BRU",
                                "at": "2025-05-16T06:25:00"
                            },
                            "arrival": {
                                "iataCode": "CDG",
                                "terminal": "1",
                                "at": "2025-05-16T07:30:00"
                            },
                            "carrierCode": "SN",
                            "number": "3631",
                            "aircraft": {
                                "code": "320"
                            },
                            "operating": {
                                "carrierCode": "SN"
                            },
                            "duration": "PT1H5M",
                            "id": "17",
                            "numberOfStops": 0,
                            "blacklistedInEU": false
                        }
                    ]
                }
            ],
            "price": {
                "currency": "XOF",
                "total": "1207300.00",
                "base": "1027300.00",
                "fees": [
                    {
                        "amount": "0.00",
                        "type": "SUPPLIER"
                    },
                    {
                        "amount": "0.00",
                        "type": "TICKETING"
                    }
                ],
                "grandTotal": "1207300.00"
            },
            "pricingOptions": {
                "fareType": [
                    "PUBLISHED"
                ],
                "includedCheckedBagsOnly": true
            },
            "validatingAirlineCodes": [
                "SN"
            ],
            "travelerPricings": [
                {
                    "travelerId": "1",
                    "fareOption": "STANDARD",
                    "travelerType": "ADULT",
                    "price": {
                        "currency": "XOF",
                        "total": "1207300.00",
                        "base": "1027300.00"
                    },
                    "fareDetailsBySegment": [
                        {
                            "segmentId": "16",
                            "cabin": "BUSINESS",
                            "fareBasis": "PNCOWCI",
                            "brandedFare": "BUSSAVERA",
                            "brandedFareLabel": "BUSINESS SAVER",
                            "class": "P",
                            "includedCheckedBags": {
                                "quantity": 2
                            },
                            "includedCabinBags": {
                                "quantity": 2
                            },
                            "amenities": [
                                {
                                    "description": "SNACK",
                                    "isChargeable": false,
                                    "amenityType": "MEAL",
                                    "amenityProvider": {
                                        "name": "BrandedFare"
                                    }
                                },
                                {
                                    "description": "COMPLIMENTARY FOOD AND BEV",
                                    "isChargeable": false,
                                    "amenityType": "MEAL",
                                    "amenityProvider": {
                                        "name": "BrandedFare"
                                    }
                                },
                                {
                                    "description": "PRIORITY CHECK IN",
                                    "isChargeable": false,
                                    "amenityType": "TRAVEL_SERVICES",
                                    "amenityProvider": {
                                        "name": "BrandedFare"
                                    }
                                },
                                {
                                    "description": "PRIORITY BOARDING",
                                    "isChargeable": false,
                                    "amenityType": "TRAVEL_SERVICES",
                                    "amenityProvider": {
                                        "name": "BrandedFare"
                                    }
                                },
                                {
                                    "description": "PRIORITY BAGGAGE",
                                    "isChargeable": false,
                                    "amenityType": "TRAVEL_SERVICES",
                                    "amenityProvider": {
                                        "name": "BrandedFare"
                                    }
                                },
                                {
                                    "description": "PRIORITY SECURITY",
                                    "isChargeable": false,
                                    "amenityType": "TRAVEL_SERVICES",
                                    "amenityProvider": {
                                        "name": "BrandedFare"
                                    }
                                },
                                {
                                    "description": "STANDARD SEAT RESERVATION",
                                    "isChargeable": false,
                                    "amenityType": "BRANDED_FARES",
                                    "amenityProvider": {
                                        "name": "BrandedFare"
                                    }
                                }
                            ]
                        },
                        {
                            "segmentId": "17",
                            "cabin": "BUSINESS",
                            "fareBasis": "PNCOWCI",
                            "brandedFare": "BUSSAVERA",
                            "brandedFareLabel": "BUSINESS SAVER",
                            "class": "P",
                            "includedCheckedBags": {
                                "quantity": 2
                            },
                            "includedCabinBags": {
                                "quantity": 2
                            },
                            "amenities": [
                                {
                                    "description": "SNACK",
                                    "isChargeable": false,
                                    "amenityType": "MEAL",
                                    "amenityProvider": {
                                        "name": "BrandedFare"
                                    }
                                },
                                {
                                    "description": "COMPLIMENTARY FOOD AND BEV",
                                    "isChargeable": false,
                                    "amenityType": "MEAL",
                                    "amenityProvider": {
                                        "name": "BrandedFare"
                                    }
                                },
                                {
                                    "description": "PRIORITY CHECK IN",
                                    "isChargeable": false,
                                    "amenityType": "TRAVEL_SERVICES",
                                    "amenityProvider": {
                                        "name": "BrandedFare"
                                    }
                                },
                                {
                                    "description": "PRIORITY BOARDING",
                                    "isChargeable": false,
                                    "amenityType": "TRAVEL_SERVICES",
                                    "amenityProvider": {
                                        "name": "BrandedFare"
                                    }
                                },
                                {
                                    "description": "PRIORITY BAGGAGE",
                                    "isChargeable": false,
                                    "amenityType": "TRAVEL_SERVICES",
                                    "amenityProvider": {
                                        "name": "BrandedFare"
                                    }
                                },
                                {
                                    "description": "PRIORITY SECURITY",
                                    "isChargeable": false,
                                    "amenityType": "TRAVEL_SERVICES",
                                    "amenityProvider": {
                                        "name": "BrandedFare"
                                    }
                                },
                                {
                                    "description": "STANDARD SEAT RESERVATION",
                                    "isChargeable": false,
                                    "amenityType": "BRANDED_FARES",
                                    "amenityProvider": {
                                        "name": "BrandedFare"
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        },
    
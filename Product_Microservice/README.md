{
   "name": "1812-100GPD Membrane",
   "description": "The 100 GPD Reverse Osmosis Membrane is engineered to deliver exceptional water purification performance for domestic and light commercial RO systems. Designed to effectively remove dissolved salts, heavy metals, bacteria, viruses, and other contaminants, it produces clean, safe, and great-tasting drinking water while maintaining consistent permeate flow.Manufactured for durability and efficiency, this membrane operates under standard test conditions with a 250 ppm NaCl feed solution, 15% recovery rate, and supports a maximum operating pressure of 21 bar (300 psi). It is compatible with most standard 100 GPD RO housings, making it an ideal replacement membrane for residential drinking water systems.",
   "brand": "Hidrotek",
   "category": "Water treatment",
   "sub_category": "Membrane",
   "application": [
       "Residential drinking water systems",
       "Water dispensers",
       "Under-sink RO units",
       "Small commercial water purification systems"
   ],
   "price": 3000,
   "meta:": {
       "title": "High-performance 100 GPD reverse osmosis membrane for reliable, high-purity water purification.",
       "description": "The 100 GPD Reverse Osmosis Membrane is engineered to deliver exceptional water purification performance for domestic and light commercial RO systems. Designed to effectively remove dissolved salts, heavy metals, bacteria, viruses, and other contaminants, it produces clean, safe, and great-tasting drinking water while maintaining consistent permeate flow."
   },
   "packing_dimensions": {
           "length": {
               "value": 31,
               "unit": "cm"
           },
           "width": {
               "value": 31,
               "unit": "cm"
           },
           "height": {
               "value": 31,
               "unit": "cm"
           },
           "weight": {
               "value": 20,
               "unit": "kg"
           }
   },
   "specifications": {
       "flow_rate": {
               "value": 100,
               "unit": "gpd"
       },
       "working_test_conditions": {
               "value": "2500 - 250",
               "unit": "ppm"
       },
           "pressure_range": {
               "value": "8 - 21",
               "unit": "bar"
       },
       "temperature": {
               "value": "20 - 45",
               "unit": "K"
       },
           "service_life": {
               "value": 365,
               "unit": "ltrs"
       },
       "details":{
                   "dimensions": {
                       "value": "A=298 C=17 B=44.5",
                       "unit": "mm"
                   },
                   "weight": {
                       "value": 500,
                       "unit": "mg"
                   },
                   "material": {
                       "value": "Membrane",
                       "unit": "chemical material"
                   }
           }
   }
}

## Hybrid Django + Mongo Product Flow

The Django backend remains the source of truth for catalogue identity, categories, partner stock records, prices, and price snapshots. This microservice stores domain-specific engineering specifications for product classes that need richer MongoDB documents.

Supported domain product classes:

- `filter` -> `Filter`
- `blower` -> `Blower`
- `chemical` -> `Chemical`
- `controller` -> `controller`
- `desalination_system` / `desalination systems` -> `desalinationsystem`
- `flow_meter` / `flow meter` -> `flowmeter`
- `plumbing_fitting` / `plumbing fittings` -> `plumbingfitting`
- `sterilizer` -> `sterilizer`
- `surface_pump` / `surface pumps` -> `SurfacePump`
- `submersible_pump` / `submersible pumps` -> `SubmersiblePump`
- `vessel` -> `vessel`

`PumpSpares.js` is currently empty, so it is not routed until it defines and exports a schema.

Configure Django with:

```env
PRODUCT_MICROSERVICE_BASE_URL=http://127.0.0.1:3029
PRODUCT_MICROSERVICE_TIMEOUT_SECONDS=8
```

Write flow:

```text
DRF ProductWriteSerializer
  -> ProductService validates and saves Django Product, Partner, StockRecord, price snapshot
  -> ProductDomainRouter maps product_class to a Mongoose discriminator
  -> Product_Microservice creates or patches the Mongo document
  -> Django stores mongo_id in accounts.ProductMongoReference
```

Read flow:

```text
Django product detail
  -> relational catalogue payload
  -> ProductService loads ProductMongoReference
  -> fetches latest Mongo document when available
  -> falls back to cached payload if the microservice is offline
```

Hybrid create/update requests can include `domain_specs`:

```json
{
  "upc": "PUMP-001",
  "title": "Surface Pump 1HP",
  "description": "Industrial surface pump",
  "product_class": "surface_pump",
  "category_ids": [1],
  "partner_id": 1,
  "price": "12000.00",
  "currency": "KES",
  "num_in_stock": 6,
  "domain_specs": {
    "brand": "Norwa",
    "packing_dimensions": {
      "length": { "value": 31, "unit": "cm" }
    },
    "specifications": {
      "max_flow_rate": { "value": 60, "unit": "lpm" }
    }
  }
}
```

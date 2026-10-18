# Real-Source Data Pack

This folder documents the CNG Real-Source Data Pack supplied for the project. The original ZIP includes station directory records, a Gujarat CNG-flagged outlet subset, a source register, a data dictionary, and blank templates for historical sales and station capacity.

## Files expected in this folder

- `gujarat_gas_directory_344_records.csv` — 344 records extracted from a Gujarat Gas station directory. Current operating status and most coordinates are not independently verified.
- `gujarat_cgd_cng_flagged_outlets_1510.csv` — 1,510 Gujarat outlet records marked `has_cng=True` in the supplied CGD mapping data. This flag does not prove the station currently dispenses CNG.
- `source_register.csv` — source URLs and limitations.
- `data_dictionary.csv` — key field definitions and caveats.
- `station_daily_sales_template_blank.csv` — blank template for verified daily sales.
- `station_capacity_template_blank.csv` — blank template for verified capacity.

## Important data limitations

- The 344-record directory has 16 provisional coordinate matches and 328 rows without coordinates. Validate coordinates before distance, catchment, or cannibalization analysis.
- This pack does not contain actual station-wise daily sales or verified station capacity.
- Do not invent missing sales, capacity, operational status, supply, queue, or company data.
- Keep synthetic demo data separate and label it clearly.
- Record the source, retrieval date, units, and any transformations.

## Source pack

The ZIP supplied for this project is not automatically committed as a binary archive through this GitHub integration. Upload the CSV files from the ZIP into this folder through GitHub's **Add file → Upload files** flow, or use Git locally. Do not upload a ZIP if the team needs to read and process the individual CSVs.

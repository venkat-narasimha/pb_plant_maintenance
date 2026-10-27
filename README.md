# Plant Maintenance for ERPNext

`pb_plant_maintenance` is a custom Frappe application that adds plant maintenance
management to ERPNext. It provides equipment and functional-location records,
maintenance notifications and orders, work confirmations, preventive plans,
measuring points, reports, and maintenance APIs.

The app integrates with ERPNext Assets, Workstations, Stock, and Accounting. It
supports multiple companies: maintenance records carry a company, and accounting
and stock vouchers use the company on the source maintenance record. Keep linked
Equipment, Cost Centers, and accounts configured for the same company.

## Compatibility

- Frappe Framework 15
- ERPNext 15
- Python 3.10 or later (provided through the Bench environment)

Frappe and ERPNext are managed by Bench and are not installed as standalone
Python dependencies by this app.

## Installation

From your Bench directory, get the app from this repository and install it on
the target site:

```bash
bench get-app https://github.com/venkat-narasimha/pb_plant_maintenance
bench --site <site-name> install-app pb_plant_maintenance
bench --site <site-name> migrate
```

After installation, assign the appropriate PM roles to users and configure PM
Settings, including the default cost center and labor expense account. For
multi-company use, verify that each maintenance record and its linked accounting
records belong to the intended company.

## Updating

From your Bench directory:

```bash
cd apps/pb_plant_maintenance
git pull
cd ../..
bench --site <site-name> migrate
bench build --app pb_plant_maintenance
bench restart
```

## Development

Run the app tests against a configured Bench site:

```bash
bench --site <site-name> run-tests --app pb_plant_maintenance
```

This repository uses pre-commit for formatting and lint checks. Install and
enable it from the app repository:

```bash
cd apps/pb_plant_maintenance
pre-commit install
pre-commit run --all-files
```

Ruff is configured for Python. Pre-commit also runs JSON/YAML/TOML and Python
checks, Prettier, and ESLint where applicable.

## Documentation

See [the handover guide](docs/handover_documentation.html) for the DocType
inventory, workflows, roles, integrations, reports, scheduled tasks, API
reference, and operations runbook.

## License

MIT. See [license.txt](license.txt).

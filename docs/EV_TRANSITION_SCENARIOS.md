# EV Transition Scenario Module

## Purpose

The EV Transition Scenario Planner adds a long-term market-transition lens to CNG network expansion decisions. It is a stress-testing tool, not an EV adoption forecasting model.

## External market context

Primary source: https://www.ibef.org/industry/electric-vehicle

Source checked: 4 November 2026.

IBEF reports:

- FY26 EV sales of 2.66 million units and 8.62% penetration of total automotive sales.
- Two- and three-wheelers represented nearly 87% of FY26 EV volumes.
- 29,151 public charging stations were reported as of December 2025.

These indicators support the relevance of testing future mobility-transition risk. They do not quantify how much CNG demand any individual Gujarat station will lose.

## Model treatment

The module applies a transparent user-selected annual EV displacement assumption:

`next_demand = current_demand × (1 + annual_cng_growth) × (1 − annual_ev_displacement)`

Presets are deliberately labelled as hypothetical planning assumptions:

- Baseline: 0% annual EV displacement
- Moderate EV adoption: 4%
- Accelerated electrification: 9%

The preset values are not sourced as station-level forecasts and can be changed by the user.

## Decision guardrails

- Do not describe scenario output as actual Gujarat Gas demand.
- Do not infer a direct one-to-one substitution between national EV sales and CNG sales.
- Vehicle segment, geography, charging access and fleet composition can materially change the impact.
- Use the output alongside the project's forecast, GIS and A/B/C expansion analysis.

## API

- `GET /api/ev-scenarios/presets`
- `POST /api/ev-scenarios/run`

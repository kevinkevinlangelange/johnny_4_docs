# johnny_4_docs

System-level documentation for the Johnny 4 robot: everything that spans more than one board repo.

## Contents

| File | What it is |
|------|------------|
| [POWER.md](POWER.md) | Power distribution for the robot side: which pin each board takes 5V on, buck converter zones, USB flashing/backfeed rules, budget |
| [j4_master_pin_diagram.pdf](j4_master_pin_diagram.pdf) | All seven boards' pin diagrams, one full letter page each, printable as one document |
| [tools/gen_master_pin_pdf.py](tools/gen_master_pin_pdf.py) | Regenerates the master PDF (and the standalone j4_controller pin diagram) from the board repos' READMEs |
| [tools/gen_poster.py](tools/gen_poster.py) | Regenerates the interconnect poster (poster PDF pulled from the repo 2026-08-14, was out of date; regenerate before re-adding) |

## Regenerating the master pin diagram

The generator parses each repo README's `## Pin diagram` fenced block and `## Pin assignments` table, so the PDF always matches the repos. After changing any pinout, update that repo's README and run:

```bash
python tools/gen_master_pin_pdf.py
```

Requires `reportlab`. The script expects the board repos checked out as siblings of this repo (`../j4_controller`, `../j4_receiver`, and so on).

## The board repos

Signal chain: [j4_controller](https://github.com/kevinkevinlangelange/j4_controller) --ESP-NOW--> [j4_receiver](https://github.com/kevinkevinlangelange/j4_receiver) --UART--> [j4_stepper_neck](https://github.com/kevinkevinlangelange/j4_stepper_neck) --UART--> [j4_stepper_eyes](https://github.com/kevinkevinlangelange/j4_stepper_eyes), with [j4_talk](https://github.com/kevinkevinlangelange/j4_talk) on the receiver's second UART and [j4_display_left](https://github.com/kevinkevinlangelange/j4_display_left) + [j4_display_right](https://github.com/kevinkevinlangelange/j4_display_right) on the controller's UARTs. Printable parts live in [johnny_4_3D_printable_parts](https://github.com/kevinkevinlangelange/johnny_4_3D_printable_parts).

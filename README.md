# NetOps Workbench

A desktop networking toolkit for **Windows and Linux**.  
This is my **first networking tool project** — built to learn by doing while staying practical.

## Modules
- **Subnet Planner** – Calculate IPv4 details (CIDR, mask, wildcard, ranges).
- **VLSM Designer** – Allocate subnets from a base network with minimal waste.
- **Scanner** – ICMP sweep, ARP (LAN), and optional Nmap (configurable).
- **PCAP Analyzer** – Open `.pcap/.pcapng`, filter, and view quick stats.
- **Firewall Simulator** – Ordered allow/deny rules with a test packet.
- **DNS Toolkit** – A/AAAA (and more with `dnspython`).
- **Cisco IOS Helper** – Generate common IOS config snippets.

## Requirements
- Python 3.10+ (3.11/3.12/3.13 OK)
- `wxPython` (GUI)
- Optional: `scapy` (PCAP parsing), `dnspython` (DNS), **Nmap** (scanner)

## Install & Run

### Windows (PowerShell or Command Prompt)
```bat
# From project root
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
# Optional modules
pip install scapy dnspython
# If you'll use the Nmap scanner, install Nmap from nmap.org and ensure nmap.exe is on PATH
python -m netops.app
```

### Linux (Ubuntu/Debian)
```bash
# From project root
python3 -m venv venv
source venv/bin/activate
# wxPython: prefer distro package for easiest setup
sudo apt update
sudo apt install -y python3-wxgtk4.0
pip install -r requirements.txt  # will skip wx if already satisfied
pip install -e .
# Optional modules
pip install scapy dnspython
# If using Nmap features
sudo apt install -y nmap
python -m netops.app
```

### Linux (Fedora)
```bash
python3 -m venv venv
source venv/bin/activate
sudo dnf install -y python3-wxpython4 nmap
pip install -r requirements.txt
pip install -e .
pip install scapy dnspython
python -m netops.app
```

## Usage Tips
- **Scanner → Nmap**: choose SYN/Connect/UDP, set `-sV`, `-O`, `-Pn`, timing `T0..T5`, and ports or top-ports. The command line used appears in the panel.
- **PCAP Analyzer**: open a file and filter by protocol (`tcp`, `udp`, `icmp`, `dns`, `http`, `tls`), IP, port, or text.
- **VLSM**: enter a base CIDR and host requirements; outputs packed allocations and any remaining gaps.
- **IOS Helper**: pick a template, fill fields, click **Generate**, then **Copy to Clipboard**.

## Packaging (optional)
Use PyInstaller once you’re happy with the build:
```bash
pip install pyinstaller
# Windows
pyinstaller -F -w launch.py
# Linux
pyinstaller -F -w launch.py
```

## License
MIT

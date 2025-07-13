import os
import json

from structlog import get_logger

SYMBOL_LIBRARY_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../arx-symbol-library'))

def load_symbol_library(search=None, category=None):
    symbols = []
    for fname in os.listdir(SYMBOL_LIBRARY_PATH):
        if fname.endswith('.json'):
            fpath = os.path.join(SYMBOL_LIBRARY_PATH, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if not data:
                        continue
                    # Add filename as symbol_id if not present
                    if 'symbol_id' not in data:
                        data['symbol_id'] = os.path.splitext(fname)[0]
                    # Extract funding_source from properties array
                    funding_source = None
                    for prop in data.get('properties', []):
                        if prop.get('name') == 'funding_source':
                            funding_source = prop.get('description', '')
                            break
                    # If funding_source is present, add as top-level key
                    if funding_source is not None:
                        data['funding_source'] = funding_source
                    symbols.append(data)
            except Exception as e:
                # Skip files with JSON errors for now
                logger.warning("failed_to_load_symbol", filename=fname, error=str(e))
                continue
    # Filtering
    if search:
        search = search.lower()
        symbols = [s for s in symbols if search in s.get('name','').lower() or search in s.get('symbol_id','').lower()]
    if category:
        symbols = [s for s in symbols if s.get('category','').lower() == category.lower()]
    return symbols

logger = get_logger()

SVG_SYMBOLS = {
    # ========================
    # MECHANICAL (HVAC) SYSTEMS
    # ========================
    "ahu": {"system": "mechanical", "display_name": "Air Handling Unit (AHU)", "svg": '''<g id="ahu"><rect x="0" y="0" width="40" height="20" fill="#ccc" stroke="#000"/><text x="20" y="15" font-size="10" text-anchor="middle">AHU</text></g>'''},
    "rtu": {"system": "mechanical", "display_name": "Rooftop Unit (RTU)", "svg": '''<g id="rtu"><rect x="0" y="0" width="40" height="20" fill="#eee" stroke="#000"/><circle cx="10" cy="10" r="5" fill="none" stroke="#000"/><text x="30" y="15" font-size="10" text-anchor="middle">RTU</text></g>'''},
    "fcu": {"system": "mechanical", "display_name": "Fan Coil Unit (FCU)", "svg": '''<g id="fcu"><rect x="0" y="0" width="30" height="15" fill="#eee" stroke="#000"/><path d="M5,12 Q15,0 25,12" stroke="#000" fill="none"/><text x="15" y="13" font-size="8" text-anchor="middle">FCU</text></g>'''},
    "vav": {"system": "mechanical", "display_name": "VAV Box", "svg": '''<g id="vav"><rect x="0" y="0" width="20" height="20" fill="#eee" stroke="#000"/><line x1="0" y1="20" x2="20" y2="0" stroke="#000"/><text x="10" y="15" font-size="8" text-anchor="middle">VAV</text></g>'''},
    "exhaust_fan": {"system": "mechanical", "display_name": "Exhaust Fan", "svg": '''<g id="exhaust_fan"><circle cx="10" cy="10" r="10" fill="#fff" stroke="#000"/><path d="M10,0 L10,20 M0,10 L20,10" stroke="#000"/><text x="10" y="18" font-size="7" text-anchor="middle">EF</text></g>'''},
    "supply_fan": {"system": "mechanical", "display_name": "Supply Fan", "svg": '''<g id="supply_fan"><circle cx="10" cy="10" r="10" fill="#fff" stroke="#000"/><polygon points="10,2 18,10 10,18 2,10" fill="none" stroke="#000"/><text x="10" y="18" font-size="7" text-anchor="middle">SF</text></g>'''},
    "return_fan": {"system": "mechanical", "display_name": "Return Fan", "svg": '''<g id="return_fan"><circle cx="10" cy="10" r="10" fill="#fff" stroke="#000"/><polygon points="10,2 18,10 10,18 2,10" fill="none" stroke="#000"/><text x="10" y="18" font-size="7" text-anchor="middle">RF</text></g>'''},
    "boiler": {"system": "mechanical", "display_name": "Boiler", "svg": '''<g id="boiler"><ellipse cx="15" cy="10" rx="15" ry="10" fill="#fff" stroke="#000"/><text x="15" y="13" font-size="10" text-anchor="middle">B</text></g>'''},
    "chiller": {"system": "mechanical", "display_name": "Chiller", "svg": '''<g id="chiller"><rect x="0" y="0" width="30" height="15" fill="#fff" stroke="#000"/><path d="M5,7 Q15,0 25,7" stroke="#00f" fill="none"/><text x="15" y="13" font-size="8" text-anchor="middle">CH</text></g>'''},
    "cooling_tower": {"system": "mechanical", "display_name": "Cooling Tower", "svg": '''<g id="cooling_tower"><rect x="0" y="0" width="20" height="20" fill="#fff" stroke="#000"/><circle cx="10" cy="7" r="5" fill="none" stroke="#000"/><path d="M5,17 Q10,22 15,17" stroke="#00f" fill="none"/><text x="10" y="18" font-size="7" text-anchor="middle">CT</text></g>'''},
    "heat_exchanger": {"system": "mechanical", "display_name": "Heat Exchanger", "svg": '''<g id="heat_exchanger"><rect x="0" y="0" width="30" height="10" fill="#fff" stroke="#000"/><line x1="5" y1="2" x2="25" y2="8" stroke="#f00"/><line x1="5" y1="8" x2="25" y2="2" stroke="#00f"/><text x="15" y="9" font-size="7" text-anchor="middle">HX</text></g>'''},
    "supply_duct": {"system": "mechanical", "display_name": "Supply Duct", "svg": '''<g id="supply_duct"><line x1="0" y1="5" x2="30" y2="5" stroke="#00f" stroke-width="3"/></g>'''},
    "return_duct": {"system": "mechanical", "display_name": "Return Duct", "svg": '''<g id="return_duct"><line x1="0" y1="10" x2="30" y2="10" stroke="#f00" stroke-width="3" stroke-dasharray="4,2"/></g>'''},
    "exhaust_duct": {"system": "mechanical", "display_name": "Exhaust Duct", "svg": '''<g id="exhaust_duct"><line x1="0" y1="15" x2="30" y2="15" stroke="#888" stroke-width="3" stroke-dasharray="2,2"/></g>'''},
    "damper": {"system": "mechanical", "display_name": "Damper", "svg": '''<g id="damper"><rect x="0" y="0" width="20" height="6" fill="#fff" stroke="#000"/><line x1="0" y1="3" x2="20" y2="3" stroke="#000"/><line x1="10" y1="0" x2="10" y2="6" stroke="#000"/></g>'''},
    "fire_damper": {"system": "mechanical", "display_name": "Fire Damper", "svg": '''<g id="fire_damper"><rect x="0" y="0" width="20" height="6" fill="#fff" stroke="#000"/><line x1="0" y1="3" x2="20" y2="3" stroke="#f00"/><text x="10" y="5" font-size="6" text-anchor="middle">FD</text></g>'''},
    "volume_damper": {"system": "mechanical", "display_name": "Volume Damper", "svg": '''<g id="volume_damper"><rect x="0" y="0" width="20" height="6" fill="#fff" stroke="#000"/><line x1="0" y1="3" x2="20" y2="3" stroke="#00f"/><text x="10" y="5" font-size="6" text-anchor="middle">VD</text></g>'''},
    "diffuser": {"system": "mechanical", "display_name": "Diffuser", "svg": '''<g id="diffuser"><rect x="0" y="0" width="12" height="12" fill="#fff" stroke="#000"/><line x1="0" y1="0" x2="12" y2="12" stroke="#000"/><line x1="12" y1="0" x2="0" y2="12" stroke="#000"/></g>'''},
    "grille": {"system": "mechanical", "display_name": "Grille", "svg": '''<g id="grille"><rect x="0" y="0" width="12" height="12" fill="#fff" stroke="#000"/><line x1="3" y1="0" x2="3" y2="12" stroke="#000"/><line x1="9" y1="0" x2="9" y2="12" stroke="#000"/></g>'''},
    "register": {"system": "mechanical", "display_name": "Register", "svg": '''<g id="register"><rect x="0" y="0" width="12" height="12" fill="#fff" stroke="#000"/><line x1="0" y1="6" x2="12" y2="6" stroke="#000"/></g>'''},
    "thermostat": {"system": "mechanical", "display_name": "Thermostat", "svg": '''<g id="thermostat"><circle cx="6" cy="6" r="6" fill="#fff" stroke="#000"/><text x="6" y="9" font-size="7" text-anchor="middle">T</text></g>'''},
    "sensor": {"system": "mechanical", "display_name": "Sensor", "svg": '''<g id="sensor"><circle cx="6" cy="6" r="6" fill="#fff" stroke="#000"/><text x="6" y="9" font-size="7" text-anchor="middle">S</text></g>'''},

    # ========================
    # ELECTRICAL SYSTEMS
    # ========================
    "receptacle": {"system": "electrical", "display_name": "Receptacle", "svg": '''<g id="receptacle"><circle cx="10" cy="10" r="7" fill="#fff" stroke="#000"/><text x="10" y="14" font-size="8" text-anchor="middle">R</text></g>'''},
    "switch": {"system": "electrical", "display_name": "Switch", "svg": '''<g id="switch"><rect x="0" y="0" width="10" height="20" fill="#fff" stroke="#000"/><text x="5" y="15" font-size="8" text-anchor="middle">S</text></g>'''},
    "switch_3way": {"system": "electrical", "display_name": "3-Way Switch", "svg": '''<g id="switch_3way"><rect x="0" y="0" width="10" height="20" fill="#fff" stroke="#000"/><text x="5" y="15" font-size="8" text-anchor="middle">S3</text></g>'''},
    "gfci": {"system": "electrical", "display_name": "GFCI Outlet", "svg": '''<g id="gfci"><rect x="0" y="0" width="10" height="20" fill="#fff" stroke="#000"/><text x="5" y="15" font-size="8" text-anchor="middle">GFCI</text></g>'''},
    "lighting": {"system": "electrical", "display_name": "Lighting", "svg": '''<g id="lighting"><circle cx="10" cy="10" r="8" fill="#fff" stroke="#000"/><line x1="2" y1="10" x2="18" y2="10" stroke="#000"/><line x1="10" y1="2" x2="10" y2="18" stroke="#000"/></g>'''},
    "panel": {"system": "electrical", "display_name": "Panel", "svg": '''<g id="panel"><rect x="0" y="0" width="20" height="30" fill="#fff" stroke="#000"/><text x="10" y="20" font-size="8" text-anchor="middle">PNL</text></g>'''},
    "transformer": {"system": "electrical", "display_name": "Transformer", "svg": '''<g id="transformer"><rect x="0" y="0" width="20" height="20" fill="#fff" stroke="#000"/><text x="10" y="15" font-size="8" text-anchor="middle">XFMR</text></g>'''},
    "motor": {"system": "electrical", "display_name": "Motor", "svg": '''<g id="motor"><circle cx="10" cy="10" r="8" fill="#fff" stroke="#000"/><text x="10" y="14" font-size="8" text-anchor="middle">M</text></g>'''},
    "junction_box": {"system": "electrical", "display_name": "Junction Box", "svg": '''<g id="junction_box"><rect x="0" y="0" width="10" height="10" fill="#fff" stroke="#000"/><text x="5" y="8" font-size="7" text-anchor="middle">J</text></g>'''},
    "ground": {"system": "electrical", "display_name": "Ground", "svg": '''<g id="ground"><line x1="5" y1="0" x2="5" y2="10" stroke="#000"/><line x1="2" y1="10" x2="8" y2="10" stroke="#000"/><line x1="3" y1="12" x2="7" y2="12" stroke="#000"/><line x1="4" y1="14" x2="6" y2="14" stroke="#000"/></g>'''},

    # ========================
    # PLUMBING SYSTEMS
    # ========================
    "wc": {"system": "plumbing", "display_name": "Water Closet (WC)", "svg": '''<g id="wc"><rect x="0" y="0" width="10" height="15" fill="#fff" stroke="#000"/><text x="5" y="12" font-size="8" text-anchor="middle">WC</text></g>'''},
    "sink": {"system": "plumbing", "display_name": "Sink", "svg": '''<g id="sink"><rect x="0" y="0" width="15" height="10" fill="#fff" stroke="#000"/><text x="7" y="8" font-size="8" text-anchor="middle">S</text></g>'''},
    "bathtub": {"system": "plumbing", "display_name": "Bathtub", "svg": '''<g id="bathtub"><rect x="0" y="0" width="20" height="8" fill="#fff" stroke="#000"/><ellipse cx="10" cy="4" rx="8" ry="3" fill="none" stroke="#000"/><text x="10" y="7" font-size="7" text-anchor="middle">BT</text></g>'''},
    "pipe_cw": {"system": "plumbing", "display_name": "Cold Water Pipe", "svg": '''<g id="pipe_cw"><line x1="0" y1="5" x2="20" y2="5" stroke="#00f" stroke-width="3"/><text x="10" y="2" font-size="6" text-anchor="middle">CW</text></g>'''},
    "pipe_hw": {"system": "plumbing", "display_name": "Hot Water Pipe", "svg": '''<g id="pipe_hw"><line x1="0" y1="10" x2="20" y2="10" stroke="#f00" stroke-width="3"/><text x="10" y="7" font-size="6" text-anchor="middle">HW</text></g>'''},
    "pipe_hwr": {"system": "plumbing", "display_name": "Hot Water Return Pipe", "svg": '''<g id="pipe_hwr"><line x1="0" y1="15" x2="20" y2="15" stroke="#0a0" stroke-width="3"/><text x="10" y="12" font-size="6" text-anchor="middle">HWR</text></g>'''},
    "pipe_sw": {"system": "plumbing", "display_name": "Sanitary Waste Pipe", "svg": '''<g id="pipe_sw"><line x1="0" y1="20" x2="20" y2="20" stroke="#888" stroke-width="3"/><text x="10" y="17" font-size="6" text-anchor="middle">SW</text></g>'''},
    "pipe_g": {"system": "plumbing", "display_name": "Gas Pipe", "svg": '''<g id="pipe_g"><line x1="0" y1="25" x2="20" y2="25" stroke="#ff0" stroke-width="3"/><text x="10" y="22" font-size="6" text-anchor="middle">G</text></g>'''},
    "pipe_v": {"system": "plumbing", "display_name": "Vent Pipe", "svg": '''<g id="pipe_v"><line x1="0" y1="30" x2="20" y2="30" stroke="#0ff" stroke-width="3"/><text x="10" y="27" font-size="6" text-anchor="middle">V</text></g>'''},
    "valve_ball": {"system": "plumbing", "display_name": "Ball Valve", "svg": '''<g id="valve_ball"><circle cx="10" cy="10" r="8" fill="#fff" stroke="#000"/><line x1="4" y1="4" x2="16" y2="16" stroke="#000"/><line x1="16" y1="4" x2="4" y2="16" stroke="#000"/><text x="10" y="18" font-size="6" text-anchor="middle">BALL</text></g>'''},
    "valve_gate": {"system": "plumbing", "display_name": "Gate Valve", "svg": '''<g id="valve_gate"><circle cx="10" cy="10" r="8" fill="#fff" stroke="#000"/><rect x="7" y="7" width="6" height="6" fill="none" stroke="#000"/><text x="10" y="18" font-size="6" text-anchor="middle">GATE</text></g>'''},
    "valve_check": {"system": "plumbing", "display_name": "Check Valve", "svg": '''<g id="valve_check"><circle cx="10" cy="10" r="8" fill="#fff" stroke="#000"/><polyline points="6,10 10,14 14,6" fill="none" stroke="#000"/><text x="10" y="18" font-size="6" text-anchor="middle">CHK</text></g>'''},
    "valve_prv": {"system": "plumbing", "display_name": "Pressure Reducing Valve (PRV)", "svg": '''<g id="valve_prv"><circle cx="10" cy="10" r="8" fill="#fff" stroke="#000"/><text x="10" y="18" font-size="6" text-anchor="middle">PRV</text></g>'''},
    "wh": {"system": "plumbing", "display_name": "Water Heater", "svg": '''<g id="wh"><rect x="0" y="0" width="10" height="20" fill="#fff" stroke="#000"/><text x="5" y="15" font-size="8" text-anchor="middle">WH</text></g>'''},
    "pump": {"system": "plumbing", "display_name": "Pump", "svg": '''<g id="pump"><circle cx="10" cy="10" r="8" fill="#fff" stroke="#000"/><text x="10" y="14" font-size="8" text-anchor="middle">P</text></g>'''},
    "expansion_tank": {"system": "plumbing", "display_name": "Expansion Tank", "svg": '''<g id="expansion_tank"><ellipse cx="10" cy="10" rx="8" ry="5" fill="#fff" stroke="#000"/><text x="10" y="15" font-size="7" text-anchor="middle">ET</text></g>'''},
    "gi": {"system": "plumbing", "display_name": "Grease Interceptor", "svg": '''<g id="gi"><rect x="0" y="0" width="10" height="10" fill="#fff" stroke="#000"/><text x="5" y="8" font-size="7" text-anchor="middle">GI</text></g>'''},

    # ========================
    # LOW VOLTAGE SYSTEMS
    # ========================
    "lv_device": {"system": "low_voltage", "display_name": "Low Voltage Device", "svg": '''<g id="lv_device"><circle cx="10" cy="10" r="7" fill="#fff" stroke="#000"/><text x="10" y="14" font-size="8" text-anchor="middle">LV</text></g>'''},
    "lv_panel": {"system": "low_voltage", "display_name": "Low Voltage Panel (PS)", "svg": '''<g id="lv_panel"><rect x="0" y="0" width="20" height="20" fill="#fff" stroke="#000"/><text x="10" y="15" font-size="8" text-anchor="middle">PS</text></g>'''},
    "relay_module": {"system": "low_voltage", "display_name": "Relay Module", "svg": '''<g id="relay_module"><rect x="0" y="0" width="15" height="10" fill="#fff" stroke="#000"/><text x="7" y="8" font-size="7" text-anchor="middle">RM</text></g>'''},
    "terminal_block": {"system": "low_voltage", "display_name": "Terminal Block", "svg": '''<g id="terminal_block"><rect x="0" y="0" width="15" height="10" fill="#fff" stroke="#000"/><text x="7" y="8" font-size="7" text-anchor="middle">TB</text></g>'''},
    "conduit": {"system": "low_voltage", "display_name": "Conduit", "svg": '''<g id="conduit"><line x1="0" y1="5" x2="20" y2="5" stroke="#888" stroke-width="2" stroke-dasharray="4,2"/></g>'''},
    "raceway": {"system": "low_voltage", "display_name": "Raceway", "svg": '''<g id="raceway"><line x1="0" y1="10" x2="20" y2="10" stroke="#888" stroke-width="2" stroke-dasharray="2,2"/></g>'''},
    "tray": {"system": "low_voltage", "display_name": "Cable Tray", "svg": '''<g id="tray"><rect x="0" y="0" width="20" height="5" fill="#fff" stroke="#000"/><line x1="0" y1="2.5" x2="20" y2="2.5" stroke="#000"/></g>'''},

    # ========================
    # TELECOMMUNICATIONS
    # ========================
    "voice_outlet": {"system": "telecommunications", "display_name": "Voice Outlet", "svg": '''<g id="voice_outlet"><rect x="0" y="0" width="10" height="10" fill="#fff" stroke="#000"/><text x="5" y="8" font-size="7" text-anchor="middle">T</text></g>'''},
    "data_outlet": {"system": "telecommunications", "display_name": "Data Outlet", "svg": '''<g id="data_outlet"><rect x="0" y="0" width="10" height="10" fill="#fff" stroke="#000"/><text x="5" y="8" font-size="7" text-anchor="middle">D</text></g>'''},
    "voice_data_outlet": {"system": "telecommunications", "display_name": "Voice/Data Outlet", "svg": '''<g id="voice_data_outlet"><rect x="0" y="0" width="10" height="10" fill="#fff" stroke="#000"/><text x="5" y="8" font-size="7" text-anchor="middle">VD</text></g>'''},
    "wap": {"system": "telecommunications", "display_name": "Wireless Access Point (WAP)", "svg": '''<g id="wap"><circle cx="10" cy="10" r="8" fill="#fff" stroke="#000"/><path d="M10,10 m-6,0 a6,6 0 1,0 12,0 a6,6 0 1,0 -12,0" stroke="#000" fill="none"/><text x="10" y="14" font-size="8" text-anchor="middle">AP</text></g>'''},
    "patch_panel": {"system": "telecommunications", "display_name": "Patch Panel", "svg": '''<g id="patch_panel"><rect x="0" y="0" width="20" height="5" fill="#fff" stroke="#000"/><text x="10" y="4" font-size="6" text-anchor="middle">PP</text></g>'''},
    "rack": {"system": "telecommunications", "display_name": "Rack", "svg": '''<g id="rack"><rect x="0" y="0" width="10" height="30" fill="#fff" stroke="#000"/><text x="5" y="20" font-size="8" text-anchor="middle">R</text></g>'''},
    "idf": {"system": "telecommunications", "display_name": "Intermediate Distribution Frame (IDF)", "svg": '''<g id="idf"><rect x="0" y="0" width="15" height="15" fill="#fff" stroke="#000"/><text x="7" y="12" font-size="7" text-anchor="middle">IDF</text></g>'''},
    "mdf": {"system": "telecommunications", "display_name": "Main Distribution Frame (MDF)", "svg": '''<g id="mdf"><rect x="0" y="0" width="15" height="15" fill="#fff" stroke="#000"/><text x="7" y="12" font-size="7" text-anchor="middle">MDF</text></g>'''},
    "cat5": {"system": "telecommunications", "display_name": "Cat5 Cable", "svg": '''<g id="cat5"><line x1="0" y1="5" x2="20" y2="5" stroke="#0af" stroke-width="2"/><text x="10" y="2" font-size="6" text-anchor="middle">Cat5</text></g>'''},
    "cat6": {"system": "telecommunications", "display_name": "Cat6 Cable", "svg": '''<g id="cat6"><line x1="0" y1="10" x2="20" y2="10" stroke="#0af" stroke-width="2"/><text x="10" y="7" font-size="6" text-anchor="middle">Cat6</text></g>'''},
    "fo": {"system": "telecommunications", "display_name": "Fiber Optic Cable", "svg": '''<g id="fo"><line x1="0" y1="15" x2="20" y2="15" stroke="#a0f" stroke-width="2"/><text x="10" y="12" font-size="6" text-anchor="middle">FO</text></g>'''},
    "coax": {"system": "telecommunications", "display_name": "Coaxial Cable", "svg": '''<g id="coax"><line x1="0" y1="20" x2="20" y2="20" stroke="#fa0" stroke-width="2"/><text x="10" y="17" font-size="6" text-anchor="middle">Coax</text></g>'''},

    # ========================
    # FIRE ALARM SYSTEMS
    # ========================
    "pull_station": {"system": "fire_alarm", "display_name": "Pull Station", "svg": '''<g id="pull_station"><rect x="0" y="0" width="10" height="20" fill="#fff" stroke="#000"/><text x="5" y="15" font-size="8" text-anchor="middle">P</text></g>'''},
    "smoke_detector": {"system": "fire_alarm", "display_name": "Smoke Detector", "svg": '''<g id="smoke_detector"><circle cx="10" cy="10" r="7" fill="#fff" stroke="#000"/><text x="10" y="14" font-size="8" text-anchor="middle">SD</text></g>'''},
    "heat_detector": {"system": "fire_alarm", "display_name": "Heat Detector", "svg": '''<g id="heat_detector"><circle cx="10" cy="10" r="7" fill="#fff" stroke="#000"/><text x="10" y="14" font-size="8" text-anchor="middle">HD</text></g>'''},
    "horn_strobe": {"system": "fire_alarm", "display_name": "Horn/Strobe", "svg": '''<g id="horn_strobe"><rect x="0" y="0" width="20" height="10" fill="#fdd" stroke="#000"/><text x="10" y="8" font-size="8" text-anchor="middle">H/S</text></g>'''},
    "speaker": {"system": "fire_alarm", "display_name": "Speaker", "svg": '''<g id="speaker"><rect x="0" y="0" width="20" height="10" fill="#fff" stroke="#000"/><text x="10" y="8" font-size="8" text-anchor="middle">SPKR</text></g>'''},
    "control_panel": {"system": "fire_alarm", "display_name": "Fire Alarm Control Panel (FACP)", "svg": '''<g id="control_panel"><rect x="0" y="0" width="20" height="20" fill="#fff" stroke="#000"/><text x="10" y="15" font-size="8" text-anchor="middle">FACP</text></g>'''},
    "annunciator": {"system": "fire_alarm", "display_name": "Annunciator", "svg": '''<g id="annunciator"><rect x="0" y="0" width="15" height="10" fill="#fff" stroke="#000"/><text x="7" y="8" font-size="7" text-anchor="middle">ANN</text></g>'''},
    "monitor_module": {"system": "fire_alarm", "display_name": "Monitor Module", "svg": '''<g id="monitor_module"><rect x="0" y="0" width="15" height="10" fill="#fff" stroke="#000"/><text x="7" y="8" font-size="7" text-anchor="middle">MM</text></g>'''},

    # ========================
    # SECURITY SYSTEMS
    # ========================
    "motion_detector": {"system": "security", "display_name": "Motion Detector", "svg": '''<g id="motion_detector"><circle cx="10" cy="10" r="7" fill="#fff" stroke="#000"/><text x="10" y="14" font-size="8" text-anchor="middle">MD</text></g>'''},
    "glass_break": {"system": "security", "display_name": "Glass Break Sensor", "svg": '''<g id="glass_break"><polygon points="10,2 18,10 10,18 2,10" fill="#fff" stroke="#000"/><text x="10" y="14" font-size="8" text-anchor="middle">GB</text></g>'''},
    "door_contact": {"system": "security", "display_name": "Door Contact", "svg": '''<g id="door_contact"><rect x="0" y="0" width="15" height="5" fill="#fff" stroke="#000"/><text x="7" y="4" font-size="7" text-anchor="middle">DC</text></g>'''},
    "window_contact": {"system": "security", "display_name": "Window Contact", "svg": '''<g id="window_contact"><rect x="0" y="0" width="15" height="5" fill="#fff" stroke="#000"/><text x="7" y="4" font-size="7" text-anchor="middle">WC</text></g>'''},
    "card_reader": {"system": "security", "display_name": "Card Reader", "svg": '''<g id="card_reader"><rect x="0" y="0" width="10" height="15" fill="#fff" stroke="#000"/><text x="5" y="12" font-size="7" text-anchor="middle">CR</text></g>'''},
    "mag_lock": {"system": "security", "display_name": "Magnetic Lock", "svg": '''<g id="mag_lock"><rect x="0" y="0" width="15" height="5" fill="#fff" stroke="#000"/><text x="7" y="4" font-size="7" text-anchor="middle">ML</text></g>'''},
    "keypad": {"system": "security", "display_name": "Keypad", "svg": '''<g id="keypad"><rect x="0" y="0" width="10" height="15" fill="#fff" stroke="#000"/><text x="5" y="12" font-size="7" text-anchor="middle">KP</text></g>'''},
    "cctv": {"system": "security", "display_name": "CCTV Camera", "svg": '''<g id="cctv"><rect x="0" y="5" width="20" height="10" fill="#fff" stroke="#000"/><circle cx="10" cy="10" r="3" fill="#000"/><text x="10" y="18" font-size="7" text-anchor="middle">CCTV</text></g>'''},
    "ptz_camera": {"system": "security", "display_name": "PTZ Camera", "svg": '''<g id="ptz_camera"><rect x="0" y="5" width="20" height="10" fill="#fff" stroke="#000"/><circle cx="10" cy="10" r="3" fill="#000"/><text x="10" y="18" font-size="7" text-anchor="middle">PTZ</text></g>'''},
    "monitor": {"system": "security", "display_name": "Security Monitor", "svg": '''<g id="monitor"><rect x="0" y="0" width="20" height="10" fill="#fff" stroke="#000"/><text x="10" y="8" font-size="8" text-anchor="middle">MON</text></g>'''},

    # ========================
    # BUILDING CONTROLS (BAS/BMS)
    # ========================
    "ts_sensor": {"system": "building_controls", "display_name": "Temperature Sensor (TS)", "svg": '''<g id="ts_sensor"><circle cx="6" cy="6" r="6" fill="#fff" stroke="#000"/><text x="6" y="9" font-size="7" text-anchor="middle">TS</text></g>'''},
    "hs_sensor": {"system": "building_controls", "display_name": "Humidity Sensor (HS)", "svg": '''<g id="hs_sensor"><circle cx="6" cy="6" r="6" fill="#fff" stroke="#000"/><text x="6" y="9" font-size="7" text-anchor="middle">HS</text></g>'''},
    "ps_sensor": {"system": "building_controls", "display_name": "Pressure Sensor (PS)", "svg": '''<g id="ps_sensor"><circle cx="6" cy="6" r="6" fill="#fff" stroke="#000"/><text x="6" y="9" font-size="7" text-anchor="middle">PS</text></g>'''},
    "fs_sensor": {"system": "building_controls", "display_name": "Flow Sensor (FS)", "svg": '''<g id="fs_sensor"><circle cx="6" cy="6" r="6" fill="#fff" stroke="#000"/><text x="6" y="9" font-size="7" text-anchor="middle">FS</text></g>'''},
    "controller": {"system": "building_controls", "display_name": "Controller", "svg": '''<g id="controller"><rect x="0" y="0" width="15" height="10" fill="#fff" stroke="#000"/><text x="7" y="8" font-size="7" text-anchor="middle">CTRL</text></g>'''},
    "io_module": {"system": "building_controls", "display_name": "I/O Module", "svg": '''<g id="io_module"><rect x="0" y="0" width="15" height="10" fill="#fff" stroke="#000"/><text x="7" y="8" font-size="7" text-anchor="middle">I/O</text></g>'''},
    "actuator": {"system": "building_controls", "display_name": "Actuator", "svg": '''<g id="actuator"><rect x="0" y="0" width="10" height="10" fill="#fff" stroke="#000"/><text x="5" y="8" font-size="7" text-anchor="middle">ACT</text></g>'''},
    "damper_bms": {"system": "building_controls", "display_name": "BMS Damper", "svg": '''<g id="damper_bms"><rect x="0" y="0" width="20" height="6" fill="#fff" stroke="#000"/><line x1="0" y1="3" x2="20" y2="3" stroke="#000"/><text x="10" y="5" font-size="6" text-anchor="middle">DMP</text></g>'''},
    "valve_bms": {"system": "building_controls", "display_name": "BMS Valve", "svg": '''<g id="valve_bms"><circle cx="10" cy="10" r="8" fill="#fff" stroke="#000"/><text x="10" y="18" font-size="6" text-anchor="middle">VAL</text></g>'''},
    "bacnet_bus": {"system": "building_controls", "display_name": "BACnet Bus", "svg": '''<g id="bacnet_bus"><line x1="0" y1="5" x2="20" y2="5" stroke="#0a0" stroke-width="2" stroke-dasharray="4,2"/><text x="10" y="2" font-size="6" text-anchor="middle">BACnet</text></g>'''},
    "modbus_bus": {"system": "building_controls", "display_name": "Modbus Bus", "svg": '''<g id="modbus_bus"><line x1="0" y1="10" x2="20" y2="10" stroke="#a50" stroke-width="2" stroke-dasharray="2,2"/><text x="10" y="7" font-size="6" text-anchor="middle">Modbus</text></g>'''},

    # ========================
    # NETWORK SYSTEMS
    # ========================
    "router": {"system": "network", "display_name": "Router", "svg": '''<g id="router"><ellipse cx="10" cy="10" rx="10" ry="6" fill="#fff" stroke="#000"/><text x="10" y="13" font-size="8" text-anchor="middle">RTR</text></g>'''},
    "switch_network": {"system": "network", "display_name": "Network Switch", "svg": '''<g id="switch_network"><rect x="0" y="0" width="20" height="10" fill="#fff" stroke="#000"/><text x="10" y="8" font-size="8" text-anchor="middle">SW</text></g>'''},
    "firewall": {"system": "network", "display_name": "Firewall", "svg": '''<g id="firewall"><rect x="0" y="0" width="20" height="10" fill="#fff" stroke="#000"/><text x="10" y="8" font-size="8" text-anchor="middle">FW</text></g>'''},
    "ap_network": {"system": "network", "display_name": "Access Point (AP)", "svg": '''<g id="ap_network"><circle cx="10" cy="10" r="8" fill="#fff" stroke="#000"/><text x="10" y="14" font-size="8" text-anchor="middle">AP</text></g>'''},
    "rack_network": {"system": "network", "display_name": "Network Rack", "svg": '''<g id="rack_network"><rect x="0" y="0" width="10" height="30" fill="#fff" stroke="#000"/><text x="5" y="20" font-size="8" text-anchor="middle">R</text></g>'''},
    "server": {"system": "network", "display_name": "Server", "svg": '''<g id="server"><rect x="0" y="0" width="20" height="10" fill="#fff" stroke="#000"/><text x="10" y="8" font-size="8" text-anchor="middle">SRV</text></g>'''},
    "ups": {"system": "network", "display_name": "UPS", "svg": '''<g id="ups"><rect x="0" y="0" width="15" height="10" fill="#fff" stroke="#000"/><text x="7" y="8" font-size="7" text-anchor="middle">UPS</text></g>'''},
    "ethernet": {"system": "network", "display_name": "Ethernet Cable", "svg": '''<g id="ethernet"><line x1="0" y1="5" x2="20" y2="5" stroke="#0af" stroke-width="2"/><text x="10" y="2" font-size="6" text-anchor="middle">Eth</text></g>'''},
    "fiber": {"system": "network", "display_name": "Fiber Optic Cable", "svg": '''<g id="fiber"><line x1="0" y1="10" x2="20" y2="10" stroke="#a0f" stroke-width="2"/><text x="10" y="7" font-size="6" text-anchor="middle">FO</text></g>'''},

    # ========================
    # AUDIOVISUAL (AV) SYSTEMS
    # ========================
    "display": {"system": "av", "display_name": "Display", "svg": '''<g id="display"><rect x="0" y="0" width="30" height="20" fill="#fff" stroke="#000"/><text x="15" y="15" font-size="8" text-anchor="middle">DISP</text></g>'''},
    "projector": {"system": "av", "display_name": "Projector", "svg": '''<g id="projector"><rect x="0" y="0" width="20" height="10" fill="#fff" stroke="#000"/><ellipse cx="10" cy="5" rx="8" ry="3" fill="none" stroke="#000"/><text x="10" y="9" font-size="7" text-anchor="middle">PJ</text></g>'''},
    "screen": {"system": "av", "display_name": "Screen", "svg": '''<g id="screen"><rect x="0" y="0" width="30" height="5" fill="#fff" stroke="#000"/><text x="15" y="4" font-size="7" text-anchor="middle">SCR</text></g>'''},
    "speaker_av": {"system": "av", "display_name": "AV Speaker", "svg": '''<g id="speaker_av"><rect x="0" y="0" width="20" height="10" fill="#fff" stroke="#000"/><text x="10" y="8" font-size="8" text-anchor="middle">SP</text></g>'''},
    "microphone": {"system": "av", "display_name": "Microphone", "svg": '''<g id="microphone"><ellipse cx="10" cy="7" rx="4" ry="7" fill="#fff" stroke="#000"/><rect x="8" y="14" width="4" height="6" fill="#fff" stroke="#000"/><text x="10" y="20" font-size="7" text-anchor="middle">MIC</text></g>'''},
    "dsp": {"system": "av", "display_name": "DSP", "svg": '''<g id="dsp"><rect x="0" y="0" width="15" height="10" fill="#fff" stroke="#000"/><text x="7" y="8" font-size="7" text-anchor="middle">DSP</text></g>'''},
    "amplifier": {"system": "av", "display_name": "Amplifier", "svg": '''<g id="amplifier"><rect x="0" y="0" width="15" height="10" fill="#fff" stroke="#000"/><text x="7" y="8" font-size="7" text-anchor="middle">AMP</text></g>'''},
    "patch_panel_av": {"system": "av", "display_name": "AV Patch Panel", "svg": '''<g id="patch_panel_av"><rect x="0" y="0" width="20" height="5" fill="#fff" stroke="#000"/><text x="10" y="4" font-size="6" text-anchor="middle">PP</text></g>'''},
    "touch_panel": {"system": "av", "display_name": "Touch Panel", "svg": '''<g id="touch_panel"><rect x="0" y="0" width="10" height="15" fill="#fff" stroke="#000"/><text x="5" y="12" font-size="7" text-anchor="middle">TP</text></g>'''},
    "control_interface": {"system": "av", "display_name": "Control Interface", "svg": '''<g id="control_interface"><rect x="0" y="0" width="10" height="15" fill="#fff" stroke="#000"/><text x="5" y="12" font-size="7" text-anchor="middle">KP</text></g>'''},
    "source_pc": {"system": "av", "display_name": "Source PC", "svg": '''<g id="source_pc"><rect x="0" y="0" width="15" height="10" fill="#fff" stroke="#000"/><text x="7" y="8" font-size="7" text-anchor="middle">PC</text></g>'''},
    "source_mp": {"system": "av", "display_name": "Source Media Player", "svg": '''<g id="source_mp"><rect x="0" y="0" width="15" height="10" fill="#fff" stroke="#000"/><text x="7" y="8" font-size="7" text-anchor="middle">MP</text></g>'''},
    "source_src": {"system": "av", "display_name": "Source (SRC)", "svg": '''<g id="source_src"><rect x="0" y="0" width="15" height="10" fill="#fff" stroke="#000"/><text x="7" y="8" font-size="7" text-anchor="middle">SRC</text></g>'''},
    "hdmi": {"system": "av", "display_name": "HDMI Cable", "svg": '''<g id="hdmi"><line x1="0" y1="5" x2="20" y2="5" stroke="#000" stroke-width="2"/><text x="10" y="2" font-size="6" text-anchor="middle">HDMI</text></g>'''},
    "vga": {"system": "av", "display_name": "VGA Cable", "svg": '''<g id="vga"><line x1="0" y1="10" x2="20" y2="10" stroke="#00f" stroke-width="2"/><text x="10" y="7" font-size="6" text-anchor="middle">VGA</text></g>'''},
    "cat6_av": {"system": "av", "display_name": "Cat6 AV Cable", "svg": '''<g id="cat6_av"><line x1="0" y1="15" x2="20" y2="15" stroke="#0af" stroke-width="2"/><text x="10" y="12" font-size="6" text-anchor="middle">Cat6</text></g>'''},
    "xlr": {"system": "av", "display_name": "XLR Cable", "svg": '''<g id="xlr"><line x1="0" y1="20" x2="20" y2="20" stroke="#000" stroke-width="2"/><text x="10" y="17" font-size="6" text-anchor="middle">XLR</text></g>'''},
    "wpg": {"system": "av", "display_name": "Wireless Presentation Gateway (WPG)", "svg": '''<g id="wpg"><rect x="0" y="0" width="10" height="10" fill="#fff" stroke="#000"/><text x="5" y="8" font-size="7" text-anchor="middle">WPG</text></g>'''},
    "wr": {"system": "av", "display_name": "Wireless Receiver (WR)", "svg": '''<g id="wr"><rect x="0" y="0" width="10" height="10" fill="#fff" stroke="#000"/><text x="5" y="8" font-size="7" text-anchor="middle">WR</text></g>'''},
    "streaming_server": {"system": "av", "display_name": "Streaming Server", "svg": '''<g id="streaming_server"><rect x="0" y="0" width="20" height="10" fill="#fff" stroke="#000"/><text x="10" y="8" font-size="7" text-anchor="middle">STR</text></g>'''},
    "avr": {"system": "av", "display_name": "AV Receiver (AVR)", "svg": '''<g id="avr"><rect x="0" y="0" width="10" height="10" fill="#fff" stroke="#000"/><text x="5" y="8" font-size="7" text-anchor="middle">AVR</text></g>'''},
    "av_box": {"system": "av", "display_name": "AV Box", "svg": '''<g id="av_box"><rect x="0" y="0" width="10" height="10" fill="#fff" stroke="#000"/><text x="5" y="8" font-size="7" text-anchor="middle">AV</text></g>'''},
    "floor_box": {"system": "av", "display_name": "Floor Box", "svg": '''<g id="floor_box"><rect x="0" y="0" width="10" height="10" fill="#fff" stroke="#000"/><text x="5" y="8" font-size="7" text-anchor="middle">FB</text></g>'''}
}

def read_svg(svg_base64):
    try:
        # ... existing code ...
        logger.info("SVG successfully decoded and parsed.")
    except Exception as e:
        logger.error(f"Failed to decode or parse SVG: {str(e)}")
        return {"error": f"Failed to decode or parse SVG: {str(e)}"}
    # ... rest of function ...
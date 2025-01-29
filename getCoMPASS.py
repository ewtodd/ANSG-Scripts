import xml.etree.ElementTree as ET
import pandas as pd
import sys

def extract_parameter_values(xml_file, parameter_key):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    print(root.get('board'))

    global_param_values = []

    # Search within the parameters
    parameters = root.find('board').find('parameters')
    for entry in parameters.findall('entry'):
        key = entry.find('key').text
        if key == parameter_key:
            value = entry.find('value').find('value').text
            global_param_values.append(value)
    
    # Search within the channels
    channel_param_values = []

    channels = root.find('board').findall('channel')
    for channel in channels:
        channelkey = channel.find('index').text
        values = channel.find('values')
        for entry in values.findall('entry'):
            key = entry.find('key').text
            if key == parameter_key:
                value_element = entry.find('value')
                if value_element is not None:
                    value = value_element.text
                    channel_param_values.append((channelkey,value))

    return global_param_values, channel_param_values

# Fix the formatting of the energy coarse gain parameter
def format_energy_coarse_gain(value):
    if value.startswith('CHARGESENS_') and 'FC_LSB_VPP' in value:
        parts = value.split('_')
        gain_value = parts[1]
        return f"{gain_value}"
    return value

# Build the table as it is displayed in CoMPASS, print it, and return it as a df 
def build_table(xml_file):
    # Define parameter keys and their corresponding row names
    parameter_keys = {
        'SRV_PARAM_CH_ENERGY_COARSE_GAIN': 'Energy coarse gain (fC/LSB x Vpp)',
        'SRV_PARAM_CH_GATE': 'Gate (ns)',
        'SRV_PARAM_CH_GATESHORT': 'Short Gate (ns)',
        'SRV_PARAM_CH_GATEPRE': 'Pre-gate (ns)',
        'SRV_PARAM_CH_DISCR_MODE': 'Trigger Mode',
        'SRV_PARAM_CH_THRESHOLD': 'Trigger Threshold (arb.)',
        'SRV_PARAM_RECLEN': 'Record Length (ns)'
    }

    # Initialize a dictionary to hold the table data
    channel_count = 8  # Channels range from CH0 to CH7
    channels = [f'CH{i}' for i in range(channel_count)]
    data = {row_name: {channel: None for channel in channels} for row_name in parameter_keys.values()}

    # Identify enabled channels
    enabled_channels = set()
    _, enabled_values = extract_parameter_values(xml_file, 'SRV_PARAM_CH_ENABLED')
    for channelkey, value in enabled_values:
        if value == 'true':
            enabled_channels.add(f'CH{channelkey}')
    
    # Populate the dictionary with values
    for parameter_key, row_name in parameter_keys.items():
        globalvalues, chvalues = extract_parameter_values(xml_file, parameter_key)

        # Assume the global value applies to all channels unless overwritten
        global_value = globalvalues[0] if globalvalues else None
        
        if parameter_key == 'SRV_PARAM_CH_ENERGY_COARSE_GAIN' and global_value:
            global_value = format_energy_coarse_gain(global_value)

        for channel in channels:
            if channel in enabled_channels:
                data[row_name][channel] = global_value

        # Overwrite with channel-specific values if available
        for channelkey, value in chvalues:
            if parameter_key == 'SRV_PARAM_CH_ENERGY_COARSE_GAIN':
                value = format_energy_coarse_gain(value)
            channel_name = f'CH{channelkey}'
           # if channel_name in enabled_channels:
            data[row_name][channel_name] = value

    # Filter out disabled channels
    for row_name in data.keys():
        data[row_name] = {k:v for k,v in data[row_name].items() if k in enabled_channels}
    
    # Convert to DataFrame
    df = pd.DataFrame(data).T
    print(df)
    return df
# Usage: give path to filename as a system argument
xml_file = sys.argv[1] 
print("Filename: " + xml_file)
output = build_table(xml_file)

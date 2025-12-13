#!/usr/bin/env python3
import re

# Read the file
with open('ArxContribution.t.sol', 'r') as f:
    content = f.read()

# Pattern to match: variable assignment from proposeContribution call
# We need to match multiline patterns where:
# bytes32 <varname> = oracle.proposeContribution(
#     ...
# );

# Strategy: Find all patterns and replace with calculate ID before call

# First, let's find all the patterns
lines = content.split('\n')
i = 0
replacements = []

while i < len(lines):
    line = lines[i]
    
    # Look for pattern: bytes32 <varname> = oracle.proposeContribution(
    match = re.match(r'(\s+)(bytes32\s+(\w+)\s+=\s+oracle\.proposeContribution\()', line)
    if match:
        indent = match.group(1)
        var_name = match.group(3)
        
        # Find the closing parenthesis and semicolon
        call_start = i
        call_lines = [line]
        j = i + 1
        while j < len(lines):
            call_lines.append(lines[j])
            if ');' in lines[j]:
                call_end = j
                break
            j += 1
        
        # Extract the parameters from the call
        # We need BUILDING_ID, worker, amount, proof
        full_call = '\n'.join(call_lines)
        
        # Try to extract parameters (they're on separate lines)
        param_lines = call_lines[1:] # Skip first line with function name
        params = []
        for pline in param_lines:
            pline = pline.strip()
            if pline and not pline.startswith(')'):
                # Remove trailing comma
                p = pline.rstrip(',').strip()
                if p:
                    params.append(p)
        
        # Parameters are: buildingId, worker, amount, proof, signature
        if len(params) >= 4:
            building_id = params[0]
            worker = params[1]
            amount = params[2]
            proof = params[3]
            signature = params[4] if len(params) > 4 else 'signature'
            
            # Create the replacement
            new_lines = [
                f'{indent}bytes32 {var_name} = calculateContributionId({building_id}, {worker}, {amount}, {proof});',
                f'{indent}vm.prank(oracle1);', # This might need adjustment
                f'{indent}oracle.proposeContribution(',
            ]
            
            # Add parameter lines
            for k, p in enumerate(params):
                suffix = ',' if k < len(params) - 1 else ''
                new_lines.append(f'{indent}    {p}{suffix}')
            
            new_lines.append(f'{indent});')
            
            replacements.append((call_start, call_end, new_lines))
        
        i = call_end + 1
    else:
        i += 1

# Apply replacements in reverse order to maintain line numbers
for start, end, new_content in reversed(replacements):
    lines[start:end+1] = new_content

# Write back
with open('ArxContribution.t.sol', 'w') as f:
    f.write('\n'.join(lines))

print(f"Applied {len(replacements)} replacements")

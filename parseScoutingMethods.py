def parse_scouting_table(text, allBlockTextExceptLast, scoutingRunLocations):
    """
    Parse scouting table text with wrapped cell values
    
    Args:
        text (str): The text content of the scouting table
        blockHeaders (list): List of block headers to identify sections in the table
        
    Returns:
        dict: Parsed scouting table data as a dictionary
    """
    try:
        # Split the text into lines
        lines = text.split('\n')
        
        # Initialize variables
        previousHeader = []
        runInfoList = []
        currentHeaderList = []
        nextRun = 1
        recordRunInfo = False
        finalDict = []
        endEarly = False

        runCounter = 0
        currentRunBlockCount = 0

        # Iterate through each line in the text
        for line in lines:
            if not endEarly:
                # Check if the line indicates the start of a new run
                if line == "1":
                    recordRunInfo = True

                    #record previous run information, since we are starting a new run
                    if runInfoList != []:
                        previousHeader = combine_values(previousHeader, allBlockTextExceptLast)
                        runInfoList = combine_values(runInfoList, allBlockTextExceptLast)

                        finalDict.append({
                                    "blockName": ", ".join(previousHeader),
                                    "blockPage": scoutingRunLocations[currentRunBlockCount][0], 
                                    "location": scoutingRunLocations[currentRunBlockCount][1],
                                    "settings": runInfoList
                                })

                        nextRun = 1

                        currentRunBlockCount=runCounter

                    runInfoList = []
                    runInfoList.append(line)
                    nextRun += 1

                # Check if the line matches the expected run number
                elif line == str(nextRun):
                    runInfoList = combine_values(runInfoList, allBlockTextExceptLast)
                    runInfoList.append(line)
                    nextRun += 1
                    recordRunInfo = True

                

                # If starting a new run, we will need to record the new header information, since runs can go onto multiple, dont overwrite previous headers if its the same as the last one
                elif "run" in line.lower():
                    runCounter+=1

                    if previousHeader != currentHeaderList:
                        previousHeader = currentHeaderList

                    currentHeaderList = []
                    recordRunInfo = False
                    currentHeaderList.append(line)
                

                # method information marks the end of scouting data and the start of operator questions
                elif "method information" in line.lower():
                    endEarly = True
                    previousHeader = combine_values(previousHeader, allBlockTextExceptLast)

                    runInfoList = combine_values(runInfoList, allBlockTextExceptLast)
                    finalDict.append({
                                "blockName": ", ".join(previousHeader),
                                "blockPage": scoutingRunLocations[currentRunBlockCount][0], 
                                "location": scoutingRunLocations[currentRunBlockCount][1],
                                "settings": runInfoList
                            })


                # Record run information if the flag is set
                elif recordRunInfo:
                    runInfoList.append(line)

                # Append to the current header list if not recording run information
                elif not recordRunInfo:
                    currentHeaderList.append(line)

        return finalDict

    except Exception as e:
        # Handle any exceptions that occur during parsing
        print(f"An error occurred while parsing the scouting table: {e}")
        return []
    

def combine_values(row, allBlockTextExceptLast):
    """
    Combine values in a row excluding "yes", "blank", if it will make the entries 
    
    Args:
        row (list): List of values in a row
        
    Returns:
        str: Combined values as a single string
    """
    removedValues = []
    combined_values = []
    newList = row

    for value in row:
        if value != "Blank" and value.lower() != "yes" and not value.isdigit():
            combined_values.append(value)


    for i in range (len(combined_values)):
        for j in range (len(combined_values), i+1, -1):

            value = ''.join(combined_values[i:j])

            if ''.join(combined_values[i:j]) in allBlockTextExceptLast:
                if (combined_values[i]) not in removedValues:
                    newList[newList.index(combined_values[i])] = value
                    removedValues.append((combined_values[i]))

                for item in combined_values[i+1:j]:
                    if item not in removedValues:
                        newList.remove(item)
                        removedValues.append(item)

    indexes_to_remove = []
    for i in range (len(newList)):
        if "unicorn" in newList[i].lower() or ":" in newList[i].lower() or "(" in newList[i].lower() or ")" in newList[i].lower():
            indexes_to_remove.append(i)

    newList = [item for index, item in enumerate(newList) if index not in indexes_to_remove]
    return newList
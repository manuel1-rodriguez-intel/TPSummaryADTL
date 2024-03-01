import os
import tkinter as tk
import csv
import zipfile
import io

def openCSV(file,access):
    rows = []
    with open(file, access) as file:
        csvreader = csv.reader(file)
        header = next(csvreader)
        for row in csvreader:
            rows.append(row)
    #print(header)
    
    return header, rows
            
def formatFlatten(header, rows):
    KillHeader = header
    KillRows = []
    
    #Delete all non iCVminTest
    for row in rows:
        if row[1] == 'iCVminTest':
            KillRows.append(row)
            
    rows = KillRows
    KillRows = []
    
    #Add Flow to header and rows
    header.append('FLOW')
    print(header)
    for row in rows:
        test = row[3].split('_')
        row.append(test[4])
        KillRows.append(row)
    rows = []
    #filter out non End, Pre, Post, and SDTEND tests
    for row in KillRows:
        flow = row[6]
        if flow == 'END' or flow == 'PREHVQK' or flow == 'POSTHVQK' or flow == 'SDTEND':
            rows.append(row)
    #KillHeader = header[3, 0, 6, 2, 1, 4, 5]
    
    return KillHeader, KillRows
    
def collectADTL(rows):
    ADTLs = {}
    for row in rows:
        ADTLs[row[0]+'_Slope'] = row[1]
        ADTLs[row[0]+'_Intercept'] = row[2]
        ADTLs[row[0]+'_Sigma'] = row[3]
        ADTLs[row[0]+'_Steps'] = row[4]
        ADTLs[row[0]+'_VminPredSlope'] = row[6]
        ADTLs[row[0]+'_VminPredIntercept'] = row[7]
        ADTLs[row[0]+'_VminPredSteps'] = row[8]
        ADTLs[row[0]+'_VminPredOffset'] = row[9]
        ADTLs[row[0]+'_VminPredFromIntercept'] = row[10]
    return ADTLs
    
def collectVADTL(rows):
    VADTLs = {}
    for row in rows:
        VADTLs[row[3]+'_Threshold'] = row[1]
        VADTLs[row[4]+'_Threshold'] = row[1]
        VADTLs[row[3]+'_ShiftName'] = row[2]
        VADTLs[row[4]+'_ShiftName'] = row[2]        
    return VADTLs
        
def formatVminSearch(header, rows):
    NewRows = []
    
    #Delete undesireable column headers - Rows will follow in the loop
    del header[2]
    del header[2]
    del header[6]
    del header[9]
    del header[9]
    del header[9]
    del header[9]
    del header[9]
    header.append('FLOW')
    
    for row in rows:
        if row[7] == '':
            continue
        if 'vminResult:' in row[7]:
            test = row[7].split(':')
            row[7] = test[1]
        test = row[7].split(',')
        row[7] = test[0]
        flow = row[7].split('_')
        del row[2]
        del row[2]
        del row[6]
        del row[9]
        del row[9]
        del row[9]
        del row[9]
        del row[9]

        row.append(flow[3])
        NewRows.append(row)
    return header, NewRows
def combineVADTLs(header, rows, VADTLs):
    header.append('VADTLThreshold')
    header.append('VADTLShiftName')
    
    NewRows = []
    for row in rows:
        try:
            if row[9] == 'POSTHVQK' or row[9] == 'PREHVQK':
                row.append(VADTLs[row[5]+'_Threshold'])
                row.append(VADTLs[row[5]+'_ShiftName'])
            else:
                row.append('')
                row.append('')
        except KeyError:
            row.append('')
            row.append('')
        NewRows.append(row)
    return header, NewRows       
          
def combineADTLs(header, rows, ADTLs):
    header.append('VminPredSlope')
    header.append('VminPredIntercept')
    header.append('VminPredSteps')
    header.append('VminPredOffset')
    header.append('VminPredOffsetFromIntercept')
    header.append('ADTLSlope')
    header.append('ADTLIntercept')
    header.append('ADTLSigma')
    header.append('ADTLSigMult')
    
    header.append('CurrentADTLStatus')
    
    NewRows = []
    for row in rows:
        try:
            if row[9] != 'POSTHVQK':
                row.append(ADTLs[row[5]+'_VminPredSlope'])
                row.append(ADTLs[row[5]+'_VminPredIntercept'])    
                row.append(ADTLs[row[5]+'_VminPredSteps'])
                row.append(ADTLs[row[5]+'_VminPredOffset'])
                row.append(ADTLs[row[5]+'_VminPredFromIntercept'])
                row.append(ADTLs[row[5]+'_Slope'])
                row.append(ADTLs[row[5]+'_Intercept'])
                row.append(ADTLs[row[5]+'_Sigma'])
                row.append(ADTLs[row[5]+'_Steps']) 
                row.append('YES '+ADTLs[row[5]+'_Steps']+'-SIGMA')
        except KeyError:
            print("FailedToFind: "+row[5])
        NewRows.append(row)
    return header, NewRows
    
def GenerateFiles(path):
    product = path.split('\\')[-4]
    TP = path.split('\\')[-3]
    output = 'C:\\temp\\TPSummaryReports\\'+product
    File = output + '\\'+TP+'.csv'
    if not os.path.exists(output):
        os.makedirs(output)
        print("Directory Created: ", output)
    
    
    VADTLHeader, VADTLRows = openCSV(path+'DA_CAKEVADTLAudit.csv','r')
    ADTLHeader, ADTLRows = openCSV(path+'DA_CAKEIDVADTLAudit.csv','r')
    VSAHeader, VSARows = openCSV(path+'DA_VMinSearchAudit.csv', 'r')
    #KillHeader, KillRows = openCSV('DA_Flatten_Instances.csv','r')
    KillHeader = []
    KillRows = []
    with zipfile.ZipFile(path+'DA_TPL2CSV.zip', 'r') as zip_file:
        with zip_file.open('DA_Flatten_Instances.csv') as file:
            content = io.TextIOWrapper(file, 'utf-8').read()
            
            csvreader = list(csv.reader(content.splitlines()))
            #KillHeader = next(csvreader)
            #for row in csvreader:
            #    KillRows.append(row)
            KillHeader = csvreader[0]
            for i in range(1, len(csvreader)):
                KillRows.append(csvreader[i])

    #KillHeader, KillRows = formatFlatten(KillHeader,KillRows)
    
    ADTLs = collectADTL(ADTLRows)
    del ADTLHeader
    del ADTLRows
    
    VADTLs = collectVADTL(VADTLRows)
    del VADTLHeader
    del VADTLRows
        
    VSAHeader, VSARows = formatVminSearch(VSAHeader, VSARows)
    
    VSAHeader, VSARows = combineVADTLs(VSAHeader, VSARows, VADTLs)
    VSAHeader, VSARows = combineADTLs(VSAHeader, VSARows, ADTLs)
    
    with open(File, mode = 'w', newline='')as file:
        writer = csv.writer(file)
        writer.writerow(VSAHeader)
        for row in VSARows:
            writer.writerow(row)
    print("Finished writing: ", File)
            
def bucketSort(items):
    max_val = max(item[1] for item in items)
    min_val = min(item[1] for item in items)
    
    bucket_range = max(1, (max_val - min_val)/len(items))
    
    buckets = [[] for _ in range(len(items))]
    
    for title, num in items:
        index = min(len(buckets) - 1, int((num - min_val) // bucket_range))
        buckets[index].append((title, num))
        
    for bucket in buckets:
        bucket.sort(key=lambda x: x[1], reverse = True)
        
    sorted_list = []
    for bucket in reversed(buckets):
        sorted_list.extend(bucket)
    
    return sorted_list
    
def list_directory(path):
    file_list.delete(0, tk.END)
    for item in os.listdir(path):
        file_list.insert(tk.END, item)
    current_directory_label.config(text="Current Directory: " + path)

def navigate(event=None):
    selected_index = file_list.curselection()
    if selected_index:
        selected_item = file_list.get(selected_index)
        new_path = os.path.join(current_path.get(), selected_item)
        if os.path.isdir(new_path):
            current_path.set(new_path)
            list_directory(new_path)

def go_up():
    new_path = os.path.dirname(current_path.get())
    current_path.set(new_path)
    list_directory(new_path)

def ok_function():
    Reports = current_path.get()
    Reports = Reports + "\\Reports\\"
    GenerateFiles(Reports)
    

def sort_by_last_modified():
    path = current_path.get()
    if not os.path.isdir(path):
        messagebox.showerror("Error", "Invalid directory path")
        return
    items = os.listdir(path)
    #Make sorting algorithm
    Sorted = []
    for item in items:
        itemPath = path+"\\"+item
        Sorted.append((item,os.path.getctime(itemPath)))
        
    Sorted = bucketSort(Sorted)
    #list
    file_list.delete(0, tk.END)
    for item in Sorted:
        file_list.insert(tk.END, item[0])
    current_directory_label.config(text="Current Directory: " + path)
    
    
def main():
    # Initialize Tkinter
    root = tk.Tk()
    root.title("TPReportSummary")

    # Frame to hold navigation buttons
    button_frame = tk.Frame(root)
    button_frame.pack()

    # Button to go up one level
    up_button = tk.Button(button_frame, text="Up", command=go_up)
    up_button.pack(side=tk.LEFT)

    # Listbox to display directory contents
    global file_list
    file_list = tk.Listbox(root, width=50, height=20)
    file_list.pack()

    # Scrollbar for the listbox
    scrollbar = tk.Scrollbar(root, orient="vertical")
    scrollbar.config(command=file_list.yview)
    scrollbar.pack(side="right", fill="y")
    file_list.config(yscrollcommand=scrollbar.set)

    # Get initial directory path
    initial_path = "I:\\program"

    # Label to display current directory
    global current_directory_label
    current_directory_label = tk.Label(root, text="Current Directory: " + initial_path, bd=1, relief=tk.SUNKEN, anchor=tk.W)
    current_directory_label.pack(side=tk.BOTTOM, fill=tk.X)
    
    # Tkinter variable to hold current directory path
    global current_path
    current_path = tk.StringVar(value=initial_path)

    # List initial directory contents
    list_directory(initial_path)

    # Bind double-click event to navigate function
    file_list.bind("<Double-1>", navigate)

    # OK button
    ok_button = tk.Button(root, text="OK", command=ok_function)
    ok_button.pack(side=tk.RIGHT, padx=5, pady=5)

    # Cancel button
    cancel_button = tk.Button(root, text="Cancel", command=root.quit)
    cancel_button.pack(side=tk.RIGHT, padx=5, pady=5)
    
    #Sort by last modified
    sort_by_last_modified_but = tk.Button(root, text="Sort By Last Modified", command=sort_by_last_modified)
    sort_by_last_modified_but.pack(side=tk.RIGHT, padx=5, pady=5)
    
    # Run the Tkinter event loop
    root.mainloop()

if __name__ == "__main__":
    main()
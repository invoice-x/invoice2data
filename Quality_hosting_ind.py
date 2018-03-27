from tkinter import *
from tkinter import ttk
from invoice2data import extract_data
from tkFileDialog import askopenfilename


root = Tk()
root.title("invoice2data")
root.resizable(False,False)

input_label = ttk.Label(root, text = "Input")
input_entry = ttk.Entry(root, width = 20)
input_ent_but = ttk.Button(root, text = "Choose")
def input_path_com():
    Tk().withdraw()
    filename = askopenfilename()
    input_entry.delete(0,END)
    input_entry.insert(0, filename)
input_ent_but.config(command = input_path_com)
input_label.grid(row = 0, column = 0)
input_entry.grid(row = 0, column = 1)
input_ent_but.grid(row = 0, column = 2)

sample1_label = ttk.Label(root, text = " ")
sample1_label.grid(row = 1, column = 0)


output_label = ttk.Label(root, text = "Output ")
output_entry = ttk.Entry(root, width = 20)
output_label.grid(row = 2, column = 0)
output_entry.grid(row = 2, column = 1)
output_entry.insert(0, "JSON")

sample2_label = ttk.Label(root, text = " ")
sample2_label.grid(row = 3, column = 0)

submit_but = ttk.Button(root, text = "Submit")
def input_path_com():
    filename = input_entry.get()
    out_type = output_entry.get()
    out_type = out_type.lower()
    out_file = "output" + "." + out_type
    result = extract_data(filename)
    out_file_open = open(out_file, 'a+')
    out_file_open.write(str(result) + "\n")
    out_file_open.close()

    result = dict(result)
    i = 1
    billed_sum = 0
    out_file_open = open("Quality Hosting.txt", 'a+')

    while i > 0:
        try:
            billed_sum = billed_sum + result['lines'][i]['price']
            out_file_open.write("Item " + str(i) + " = " + str(result["lines"][i]['price']) + "\n")
            i = i + 1
        except:
            break
    out_file_open.write("Total Bill = " + str(billed_sum) + "\n")
    print (billed_sum)
    out_file_open.close()


 #-----------------------------------------------------------
 #"""To be completed soon after getting a test file"""
submit_but.config(command = input_path_com)
submit_but.grid(row = 4, column = 1)
root.mainloop()

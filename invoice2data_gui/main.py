import csv
import json
import getpass
from os.path import join
from tkinter.filedialog import askopenfilename
from tkinter import StringVar
from tkinter import Tk
from tkinter import ttk
from dicttoxml import dicttoxml
from invoice2data import extract_data

def draw_gui():
    root = Tk()
    root.title("invoice2data GUI")
    root.resizable(False, False)
#Function to take input of file
    def input_path_com():
        Tk().withdraw()
        filename = askopenfilename()
        input_entry.delete(0, "")
        input_entry.insert(0, filename)
#Function to process data and save it on Desktop
    def submit_com():
        filename = input_entry.get()
        status_entry.delete(0, "")
        status_entry.insert(0, "Cheking for file")

        content = extract_data(filename)

        if str(content) == "False":
            status_entry.delete(0, "")
            status_entry.insert(0, "File Error!!!")

        else:
            file_type = list_option.get()
            file_type = file_type.lower()
            file_name = "output." + file_type

            if file_type == "xml":
                content = dicttoxml(content, custom_root='test', attr_type=False)

                try:
                    username = getpass.getuser()
                    path = "/home/" + username + "/Desktop"
                    out_file_open = open(join(path, file_name), 'w')
                    out_file_open.write(str(content))
                    out_file_open.close()
                    status_entry.delete(0, "")
                    status_entry.insert(0, "Check Desktop")
                    input_entry.delete(0, "")

                except:
                    out_file_open = open((file_name), 'w')
                    out_file_open.write(str(content))
                    out_file_open.close()
                    status_entry.delete(0, "")
                    status_entry.insert(0, ("Successfully written in " + file_name))
                    input_entry.delete(0, "")

            if file_type == "csv":
                try:
                    username = getpass.getuser()
                    path = "/home/" + username + "/Desktop"
                    with open(join(path, file_name), 'wb') as file_opner:  # Just use 'w' mode in 3.x
                        file_csv = csv.DictWriter(file_opner, content.keys())
                        file_csv.writeheader()
                        file_csv.writerow(content)
                    status_entry.delete(0, "")
                    status_entry.insert(0, "Check Desktop")
                    input_entry.delete(0, "")

                except:
                    with open((file_name), 'w') as file_opner:  # Just use 'w' mode in 3.x
                        file_csv = csv.DictWriter(file_opner, content.keys())
                        file_csv.writeheader()
                        file_csv.writerow(content)
                    status_entry.delete(0, "")
                    status_entry.insert(0, ("Successfully written in " + file_name))
                    input_entry.delete(0, "")

            if file_type == "json":
                try:
                    username = getpass.getuser()
                    path = "/home/" + username + "/Desktop"
                    out_file_open = open(join(path, file_name), 'w')
                    out_file_open.write(str(content))
                    out_file_open.close()
                    status_entry.delete(0, "")
                    status_entry.insert(0, "Check Desktop")
                    input_entry.delete(0, "")

                except:
                    out_file_open = open((file_name), 'w')
                    out_file_open.write(str(content))
                    out_file_open.close()
                    status_entry.delete(0, "")
                    status_entry.insert(0, ("Successfully written in " + file_name))
                    input_entry.delete(0, "")
#GUI started
    input_label = ttk.Label(root, text="Invoice File:")
    input_entry = ttk.Entry(root, width=20)
    input_ent_but = ttk.Button(root, text="Select")
    input_ent_but.config(command=input_path_com)
    input_label.grid(row=0, column=0)
    input_entry.grid(row=0, column=1)
    input_ent_but.grid(row=0, column=2)

    sample1_label = ttk.Label(root, text=" ")
    sample1_label.grid(row=1, column=0)

    output_label = ttk.Label(root, text="Output Format")
    list_option = StringVar(root)
    list_option.set("JSON")
    output_type = ttk.OptionMenu(root, list_option, 'JSON', 'JSON', 'CSV', 'XML')
    output_label.grid(row=2, column=0)
    output_type.grid(row=2, column=1)

    sample2_label = ttk.Label(root, text=" ")
    sample2_label.grid(row=3, column=0)

    submit_but = ttk.Button(root, text="Extract")
    submit_but.config(command=submit_com)
    submit_but.grid(row=4, column=1)

    sample3_label = ttk.Label(root, text=" ")
    sample3_label.grid(row=6, column=0)

    status_label = ttk.Label(root, text='Status')
    status_entry = ttk.Entry(root, width=20)
    status_label.grid(row=7, column=0)
    status_entry.grid(row=7, column=1)

    root.mainloop()

def main():
    draw_gui()


if __name__ == '__main__':
    main()

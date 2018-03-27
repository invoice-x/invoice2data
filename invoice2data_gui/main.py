from tkinter import Tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename
from invoice2data import extract_data


def draw_gui():
    root = Tk()
    root.title("invoice2data GUI")
    root.resizable(False, False)

    input_label = ttk.Label(root, text="Invoice File:")
    input_entry = ttk.Entry(root, width=20)
    input_ent_but = ttk.Button(root, text="Select")

    def input_path_com():
        Tk().withdraw()
        filename = askopenfilename()
        input_entry.delete(0, "")
        input_entry.insert(0, filename)

    input_ent_but.config(command=input_path_com)
    input_label.grid(row=0, column=0)
    input_entry.grid(row=0, column=1)
    input_ent_but.grid(row=0, column=2)

    sample1_label = ttk.Label(root, text=" ")
    sample1_label.grid(row=1, column=0)

    output_label = ttk.Label(root, text="Output Format")
    output_type_label = ttk.Label(root, text="JSON")
    output_label.grid(row=2, column=0)
    output_type_label.grid(row=2, column=1)

    sample2_label = ttk.Label(root, text=" ")
    sample2_label.grid(row=3, column=0)

    submit_but = ttk.Button(root, text="Extract")

    def submit_com():
        filename = input_entry.get()
        status_entry.delete(0, "")
        status_entry.insert(0, "Cheking for file")

        try:
            result = extract_data(filename)
            status_entry.delete(0, "")
            status_entry.insert(0, "File Found")
        except:
            status_entry.delete(0, "")
            status_entry.insert(0, "File Error!!!")

        out_file_open = open('output.json', 'w')
        out_file_open.write(str(result))
        out_file_open.close()

        status_entry.delete(0, "")
        status_entry.insert(0, "Successfully extracted to 'output.json'")
        input_entry.delete(0, "END")

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

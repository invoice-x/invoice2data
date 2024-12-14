Frequently asked Questions
==========================

## Can invoice2data output ubl compliant invoices?

While invoice2data is excellent at extracting data from invoices, it currently cannot output fully compliant UBL (Universal Business Language) invoices. Here's why:

* **Focus on Data Extraction:** invoice2data is primarily designed for extracting key information like invoice number, dates, amounts, and line items. Its strength lies in parsing diverse invoice layouts and formats to capture this data.
* **UBL Complexity:** UBL is a comprehensive XML-based standard for electronic business documents. It has a rigid structure with many required fields and specific data types for representing various business processes, including invoicing. Creating a valid UBL invoice requires adhering to these intricate specifications.
* **Missing Business Context:** invoice2data extracts data without fully understanding the underlying business context. It doesn't have the capability to infer or generate information like payment terms, tax codes, or detailed product descriptions, which are often essential for a compliant UBL invoice.
* **Limited Semantic Understanding:**  While invoice2data uses templates and regex to identify data, it doesn't truly understand the semantics of an invoice. It can't automatically map extracted information to the correct UBL elements or handle complex business rules that might influence the UBL representation.

**In summary:** invoice2data excels at extracting data, but generating a fully compliant UBL invoice requires a deeper understanding of the business context, semantic mapping of the data to UBL elements, and adherence to the specific rules and structures of the UBL standard.

**Possible Solutions:**

* **Post-processing:** You could use invoice2data to extract the data and then use another library or tool to map this data to a UBL-compliant XML structure.
* **Template Enhancements:** Future versions of invoice2data could potentially incorporate more advanced templates or plugins to handle some aspects of UBL generation.
* **Integration with UBL Libraries:** invoice2data could be integrated with dedicated UBL libraries to facilitate the creation of compliant invoices.

Despite these limitations, invoice2data remains a valuable tool for automating data extraction from invoices. Its output can be a crucial first step in generating UBL invoices or integrating with other systems that require structured invoice data.

## What is the easiest wway to generate a invoice2data template?

The easiest way to generate an invoice2data template is to **start with an existing one and modify it.** Here's a step-by-step guide:

1. **Find a similar template:**
   - Look in the `invoice2data/extract/templates` folder within the installed package.
   - Find a template that roughly matches the structure of your invoice (e.g., similar issuer, layout, fields).

2. **Copy the template:**
   - Create a new file (e.g., `my_template.yaml`) and copy the contents of the similar template into it.

3. **Modify the template:**

   - **`issuer`:** Change this to the company name on your invoice.
   - **`keywords`:**  Identify a unique word or phrase that consistently appears on this type of invoice.
   - **Test and refine:** Use the `--debug` option with invoice2data to see how well the template works on your invoice.
   - **Adjust regex:**  Refine the regular expressions for each field to accurately capture the data from your invoice. You can use online regex testers to help with this.

**Example:**

Let's say you have an invoice from "Acme Corp." and you find a template for "Example Inc." that has a similar layout.

1. Copy the `example_inc.yaml` template to a new file named `acme_corp.yaml`.
2. Change the `issuer` field to "Acme Corp."
3. Look for a unique keyword on the Acme Corp. invoice (e.g., "Acme Invoice").
4. Run `invoice2data --debug my_invoice.pdf` to see the extracted text and how the template matches.
5. Adjust the regex for fields like `invoice_number`, `date`, `amount`, etc., to match the Acme Corp. invoice format.

**Tips:**

* **Start with simple fields:** Focus on the most important fields first (invoice number, date, total).
* **Use online regex testers:** These tools help you build and test regular expressions. e.g. [regex101.com](https://regex101.com)
* **The `--debug` option is your friend:** It shows you exactly how invoice2data is interpreting your template.
* **Don't be afraid to experiment:** Try different regex patterns and keywords until you get a good match.

By starting with an existing template and iteratively refining it, you can quickly create a template that accurately extracts data from your invoices.

## Can Gemini create invoice2data templates?

While Gemini can't directly create ready-to-use invoice2data templates yet, Gemini can definitely help you with the process! Here's how Gemini can assist:

**1. Understanding Your Invoice:**

**Provide Gemeini with an example invoice:** You can share an image or a PDF of the invoice you want to process.
Describe the key fields: Tell Gemini which fields are important to you (e.g., invoice number, date, total amount, line items, etc.).
Point out any specific challenges: If there are any particular difficulties with the invoice layout or format, let Gemini know.
**2. Generating Template Components:**

**Suggesting keywords:** Based on the invoice, Gemini can propose relevant keywords for the keywords field in the template.
Crafting regular expressions: Gemini can help you create regular expressions to extract specific data fields from the invoice.
Identifying potential issues: Gemini can analyze the invoice and point out potential challenges that might require more complex regex or template logic.
**3. Providing Template Structure:**

**YAML formatting:** Gemini can help you structure the template in the correct YAML format.
Organizing fields: Gemini can suggest how to organize the different fields and sections within the template.
Adding comments and documentation: Gemini can help you add clear comments and documentation to your template to make it easier to understand and maintain.
**4. Refining the Template:**

**Analyzing debug output:** If you provide the output of the `--debug option`, Gemini can help you analyze it and identify areas for improvement in the template.
Suggesting regex modifications: Gemini can propose modifications to your regular expressions to improve accuracy and efficiency.
Troubleshooting errors: If you encounter any errors, Gemini can help you troubleshoot them and find solutions.
Example:

You: "I have an invoice from 'ABC Company' with a strange date format. Can you help me create a template?"

Me: "Sure! Please share the invoice with me. Gemini can help you identify unique keywords and create a regex to capture that date format."

In essence, Gemini can act as your assistant in the template creation process, providing suggestions, generating code snippets, and helping you refine the template for optimal performance.

While Gemini can't fully automate the process yet, Gemini can significantly speed it up and make it easier for you to create effective invoice2data templates.

"""This module handles generating Word files from templates."""

import zipfile
import os
import shutil
from datetime import date


def replace_keywords_in_word_template(template_path: str, result_path: str, keywords_replacements: dict[str, str]):
    """Insert text into a word template.

    Args:
        template_path: The file path of the word template file.
        result_path: The file path of the resulting word file.
        keywords_replacements: A dictionary with template keywords and the text to insert.
    """
    # Create a temporary directory to extract the files
    temp_dir = "temp_zip_extraction"
    os.makedirs(temp_dir, exist_ok=True)

    # Extract all files from the zip archive
    with zipfile.ZipFile(template_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    # Iterate through all extracted files
    for root, _, files in os.walk(temp_dir):
        for file in files:
            if file.endswith(".xml"):  # Consider only xml files
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding="utf-8") as f:
                    content = f.read()
                # Replace keywords with replacements
                for keyword, replacement in keywords_replacements.items():
                    content = content.replace(keyword, replacement)
                # Write modified content back to the file
                with open(file_path, 'w', encoding="utf-8") as f:
                    f.write(content)

    # Re-zip the modified files
    with zipfile.ZipFile(result_path, 'w') as zip_ref:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                zip_ref.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), temp_dir))

    # Clean up the temporary directory
    shutil.rmtree(temp_dir)


def format_date(in_date: date) -> str:
    """Format a date object as a danish date string.
    E.g. date(2024, 1, 1) -> 1. januar 2024

    Args:
        in_date: The date object to format.

    Returns:
        A danish string representation of the date.
    """
    months = ("januar", "februar", "marts", "april", "maj", "juni", "juli", "august", "september", "oktober", "november", "december")
    return f"{in_date.day}. {months[in_date.month-1]} {in_date.year}"


# if __name__ == '__main__':
#     # Example usage:
#     zip_file_in = r"C:\Users\az68933\Desktop\temp\Din flytning er anmeldt for sent.docx"
#     zip_file_out = r"C:\Users\az68933\Desktop\temp\Din flytning er anmeldt for sent 2.docx"

#     keywords_replacements = {
#         "SENDEDATO": format_date(date.today()),
#         "ANMELDELSESDATO": format_date(date(2024, 3, 10)),
#         "FLYTTEDATO": format_date(date(2024, 3, 1)),
#         "MODTAGER_NAVN": "Pernille Hejsen",
#         "MODTAGER_BY": "2345 Hejstrup",
#         "ADRESSE": "Hejvej 2, 1234 Hejby",
#         "BELØB": "945",
#         "KONTAKT": "Mads Halløjsen",
#         "SAGSNUMMER": "S2024-12345"
#     }

#     replace_keywords_in_word_template(zip_file_in, zip_file_out, keywords_replacements)

#     os.startfile(zip_file_out)

from flask_wtf import FlaskForm
from wtforms import SubmitField, BooleanField, SelectMultipleField, TextField
from wtforms.csrf.core import CSRFTokenField

class QcSearchForm(FlaskForm):
    approved = BooleanField("Include Approved Scans", default=True,
                            render_kw={"class": "qc-search-bool"})
    blacklisted = BooleanField("Include Blacklisted Scans", default=True,
                               render_kw={"class": "qc-search-bool"})
    flagged = BooleanField("Include Flagged Scans", default=True,
                           render_kw={"class": "qc-search-bool"})
    include_phantoms = BooleanField("Include Phantoms", default=False,
                                    render_kw={"class": "qc-search-bool"})
    include_new = BooleanField("Include Scans Without Review", default=False,
                               render_kw={"class": "qc-search-bool"})
    study = SelectMultipleField("Select all studies to search",
                                render_kw={"class": "qc-search-select"})
    site = SelectMultipleField("Select all sites to search",
                               render_kw={"class": "qc-search-select"})
    tag = SelectMultipleField("Select all tags to search",
                              render_kw={"class": "qc-search-select"})
    comment = TextField(
        "Enter a semi-colon delimited list of comments to search for",
        render_kw={"class": "qc-search-text"})


def get_form_contents(form):
    """Retrieve the contents of a form (excluding fields only WTForms needs).

    Args:
        form (wtforms.form.FormMeta): An instance of a WTForm (or FlaskWTForm).

    Returns:
        dict: A dictionary of all field names mapped to their value (excluding
            any CSRFToken fields or submit fields).
    """
    contents = {}
    for fname in form._fields:
        field = form._fields[fname]
        if isinstance(field, CSRFTokenField) or isinstance(field, SubmitField):
            continue

        if fname == "comment":
            contents[fname] = parse_comment(field.data)
        else:
            contents[fname] = field.data

    return contents


def parse_comment(user_input):
    # Strip quotation marks and white space and split by semi-colon
    if not user_input:
        return []

    strip = ['"', "'"]
    search_terms = []
    for term in user_input.split(";"):
        term = term.strip()
        for item in strip:
            term = term.lstrip(item).rstrip(item)
        search_terms.append(term)
    return search_terms

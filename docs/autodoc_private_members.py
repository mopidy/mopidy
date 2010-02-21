def setup(app):
    app.connect('autodoc-skip-member', autodoc_private_members_with_doc)

def autodoc_private_members_with_doc(app, what, name, obj, skip, options):
    if not skip:
        return skip
    if (name.startswith('_') and obj.__doc__ is not None
            and not (name.startswith('__') and name.endswith('__'))):
        return False
    return skip

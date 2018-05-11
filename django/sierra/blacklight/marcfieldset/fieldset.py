"""
Model and manipulate MARC-style fields and sets of MARC-style fields.
"""

class Field(dict):
    """
    Model and manipulate a MARC-style field as a dict structure.

    Fields are just dicts with a particular structure. As it is, this
    class does not enforce or validate that structure in any way. Use
    a factory to put field data into the correct structure before a
    Field object is instantiated.

    Control fields (001 to 009) should look like this:

    {
        'tag': '007',
        'data': '98765',
        'indicators': [None, None],
        'subfields': [],
        'occurrence': 1
    }

    All other fields (010 to 999) should look like this:

    {
        'tag': '500',
        'indicators': [' ', ' '],
        'subfields': [
            {
                'tag': 'a',
                'data': 'Test note 3.'
            },
            {
                'tag': 'a',
                'data': 'Repeated subfield a.'
            },
            {
                'tag': 'c',
                'data': 'Subfield c.'
            },
        ],
        'occurrence': 9
    }

    An `occurrence` (or similar) element is optional but can be useful
    for sorting fields, especially where you have repeated fields.

    Since Fields are just dicts and Fieldsets are just lists, you can
    include other elements that you might find helpful without harming
    how the object functions.
    """

    def _shallow_copy(self):
        """
        Return a shallow copy of this field object.
        """
        new = {k: v for k, v in self.iteritems()}
        return type(self)(new)

    def subfields_where(self, test, *args, **kwargs):
        """
        Filter subfields to ones matching particular test criteria.

        Returns a shallow copy of the object that includes ONLY the
        subfields matching the test criteria. `test` is the test
        function, and `args` and `kwargs` are the arguments passed to
        the test function. If no subfields match, a field with an empty
        list in the `subfields` element is returned.

        Premade test functions are in `marcfieldset.filters`, but you
        can easily create your own. See the docstring in the
        `marcfieldset.filters` module for more information.
        """
        new = self._shallow_copy()
        new['subfields'] = [sf for sf in self['subfields']
                            if test(sf, *args, **kwargs)]
        return new

    def subfields_where_not(self, test, *args, **kwargs):
        """
        Filter subfields to ones NOT matching particular test criteria.

        Returns a shallow copy of the object that includes ONLY the
        subfields NOT matching the test criteria. `test` is the test
        function, and `args` and `kwargs` are the arguments passed to
        the test function. If NO subfields are non-matching, a field
        with an empty list in the `subfields` element is returned.

        Premade test functions are in `marcfieldset.filters`, but you
        can easily create your own. See the docstring in the
        `marcfieldset.filters` module for more information.
        """
        new = self._shallow_copy()
        new['subfields'] = [sf for sf in self['subfields']
                            if not test(sf, *args, **kwargs)]
        return new

    def replace_subfield_data(self, replace=lambda x: x):
        """
        Replace data for each subfield based on a `replace` function.

        This method replaces subfield data for each subfield on the
        current Field object by running the subfield data through the
        provided `replace` function. The `replace` function should take
        the subfield data (string) and return a replacement string.

        Returns this object (`self`).

        Note that Field and Fieldset methods pass around individual
        subfield data structures
        (e.g. {'tag': 'a', 'data': 'Subfield data.'}) by reference.
        So if you run this method on a filtered fieldset, or a field
        where you've filtered what subfields are included, then the
        data will be changed on the original unfiltered fieldset. This
        is intentional, allowing you to use filters to find the data
        you want to change and then change it in context of the larger
        fieldset. If you NEED to preserve a fieldset exactly as-is,
        you should use copy.deepcopy to copy it before you change it.
        """
        for sub in self['subfields']:
            sub['data'] = replace(sub['data'])
        return self

    def do_for_each_subfield(self, do_for_each):
        """
        Run a custom `do_for_each` function on each subfield.

        Each subfield dict is passed to your custom function. Whatever
        value your function returns is added to the results list that
        this method returns, along with the value of subfield['tag']
        and subfield['data'], both before and after the function runs.

        Note that your custom function CAN alter the subfield data
        and/or tag by modifying the subfield dict that is passed to it.
        This is by design, and this is the reason before and after
        values are returned in the results.
        """
        results = []
        for sub in self['subfields']:
            result = {'before': {'tag': sub['tag'], 'data': sub['data']}}
            result['return_value'] = do_for_each(sub)
            result['after'] = {'tag': sub['tag'], 'data': sub['data']}
            results.append(result)
        return results

    def get_subfields_as_string(self, delimiter=' '):
        """
        Return subfield data for the field as one formatted string.

        Subfields are concatenated together in the order they appear
        in self['subfields'], separated via the provided `delimiter`
        string.
        """
        return delimiter.join([sf['data'] for sf in self['subfields']])


class Fieldset(list):
    """
    Work with a list of Field objects as a filterable group.

    A Fieldset is just a list with added methods. These methods work
    under the assumption that each list item is a Field object, but the
    class itself provides no validation. Use a factory to create Field
    objects and generate a Fieldset based on the source of your MARC
    data.
    """

    def __getslice__(self, i, j):
        """
        Return a Fieldset object when slicing.

        Overriding this is only necessary to make sure slicing a
        Fieldset returns another Fieldset.
        """
        return Fieldset(super(Fieldset, self).__getslice__(i, j))

    def __add__(self, other):
        """
        Return a Fieldset object when concatenating.

        Overriding this is only necessary to make sure concatenating
        two Fieldsets returns another Fieldset. (i.e., fs1 + fs2)
        """
        return Fieldset(super(Fieldset, self).__add__(other))

    def __mul__(self, other):
        """
        Return a Fieldset object when multiplying.

        Overriding this is only necessary to make sure multiplying
        a Fieldset returns another Fieldset. (i.e., 2 * fs)
        """
        return Fieldset(super(Fieldset, self).__mul__(other))

    def fields_where(self, test, *args, **kwargs):
        """
        Filter fields to ones matching particular test criteria.

        Returns a new Fieldset object that includes ONLY the fields
        matching the test criteria. `test` is the test function, and
        `args` and `kwargs` are the arguments passed to the test
        function. If nothing matches, an empty Fieldset is returned.

        Premade test functions are in `marcfieldset.filters`, but you
        can easily create your own. See the docstring in the
        `marcfieldset.filters` module for more information.
        """
        fields = [f for f in self if test(f, *args, **kwargs)]
        return type(self)(fields)

    def fields_where_not(self, test, *args, **kwargs):
        """
        Filter fields to ones NOT matching particular test criteria.

        Returns a new Fieldset object that includes only the fields
        NOT matching the test criteria. `test` is the test function,
        and `args` and `kwargs` are the arguments passed to the test
        function. If NO fields are non-matching, an empty Fieldset is
        returned.

        Premade test functions are in `marcfieldset.filters`, but you
        can easily create your own. See the docstring in the
        `marcfieldset.filters` module for more information.
        """
        fields = [f for f in self if not test(f, *args, **kwargs)]
        return type(self)(fields)

    def subfields_where(self, test, *args, **kwargs):
        """
        Filter each field's sf list to ones matching test criteria.

        Returns a new Fieldset object where each Field's `subfields`
        list is filtered to include ONLY those matching the test
        criteria. `test` is the test function, and `args` and `kwargs`
        are the arguments passed to the test function.

        Beware that fields with NO matching subfields remain in the
        Fieldset, but their `subfields` element is an empty list.

        Premade test functions are in `marcfieldset.filters`, but you
        can easily create your own. See the docstring in the
        `marcfieldset.filters` module for more information.
        """
        fields = [f.subfields_where(test, *args, **kwargs) for f in self]
        return type(self)(fields)

    def subfields_where_not(self, test, *args, **kwargs):
        """
        Filter each field's sf list to ones NOT matching test criteria.

        Returns a new Fieldset object where each Field's `subfields`
        list is filtered to include only those NOT matching the test
        criteria. `test` is the test function, and `args` and `kwargs`
        are the arguments passed to the test function.

        Beware that fields with NO non-matching subfields remain in the
        Fieldset, but their `subfields` element is an empty list.

        Premade test functions are in `marcfieldset.filters`, but you
        can easily create your own. See the docstring in the
        `marcfieldset.filters` module for more information.
        """
        fields = [f.subfields_where_not(test, *args, **kwargs) for f in self]
        return type(self)(fields)

    def replace_subfield_data(self, replace=lambda x: x):
        """
        Replace data for each subfield in each field.

        Calls `replace_subfield_data` on each field in the fieldset,
        replacing each subfield's `data` element based on the provided
        `replace` function. Returns a new Fieldset object.
        """
        fields = [f.replace_subfield_data(replace) for f in self]
        return type(self)(fields)

    def do_for_each_subfield(self, do_for_each):
        """
        Run a custom function on each subfield of each field.

        Calls `do_for_each_subfield` on each field in the fieldset.
        Returns a list of results from all calls made.
        """
        return [f.do_for_each_subfield(do_for_each) for f in self]

    def get_subfields_as_strings(self, delimiter=' '):
        """
        Return a list of subfield strings, one for each field.

        Calls `get_subfields_as_string` on each field in the fieldset.
        Returns a list of strings.
        """
        return [f.get_subfields_as_string(delimiter) for f in self]

    def get_sorted(self, elements=None, key=None, reverse=False):
        """
        Return a sorted version of this Fieldset.

        Calls the built-in `sorted` function to do the sort. Sorts by
        (MARC) tag by default, but you can provide a custom list of
        top-level elements or a custom key function to use. Like with
        `sorted`, if `reverse` is True then it will reverse the sort
        (descending).

        Unlike the list `sort` method, this does not change the
        original Fieldset--like all the other Fieldset methods, it
        returns a new Fieldset.
        """
        elements = elements or ['tag']
        if key is None:
            key = lambda x: [x.get(el, 0) for el in elements]
        return type(self)(sorted(self, key=key, reverse=reverse))

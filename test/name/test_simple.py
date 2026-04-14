# SPDX-License-Identifier: MIT

import unittest


class TestSimpleName(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        global PersonName, SimplePersonName, NameField, FieldModifier
        from musculus.metadata.name import FieldModifier, NameField, PersonName
        from musculus.metadata.name.simple import SimplePersonName

    def test_comparison(self):
        js = SimplePersonName({NameField.GIVEN: "John", NameField.SURNAME: "Smith"})
        js2 = SimplePersonName({NameField.GIVEN: "John", NameField.SURNAME: "Smith"})
        jqs = SimplePersonName({NameField.GIVEN: "John Q.", NameField.SURNAME: "Smith"})
        self.assertEqual(js, js2)
        self.assertNotEqual(js, jqs)

    def test_bibtex_parse(self):
        # Names taken from https://metacpan.org/pod/LaTeX::BibTeX::Name#EXAMPLES
        cases = {
            "John Smith": {NameField.GIVEN: "John", NameField.SURNAME: "Smith"},
            "Smith, John": {NameField.GIVEN: "John", NameField.SURNAME: "Smith"},
            "John Q. Smith": {NameField.GIVEN: "John Q.", NameField.SURNAME: "Smith"},
            "J. R. R. Tolkein": {
                NameField.GIVEN: "J. R. R.",
                NameField.SURNAME: "Tolkein",
            },
            "Kevin Philips Bong": {
                NameField.GIVEN: "Kevin Philips",
                NameField.SURNAME: "Bong",
            },
            "Philips Bong, Kevin": {
                NameField.GIVEN: "Kevin",
                NameField.SURNAME: "Philips Bong",
            },
            "Kevin {Philips Bong}": {
                NameField.GIVEN: "Kevin",
                NameField.SURNAME: "{Philips Bong}",
            },
            "St John-Mollusc, Oliver": {
                NameField.GIVEN: "Oliver",
                NameField.SURNAME: "St John-Mollusc",
            },
            "Oliver {St John-Mollusc}": {
                NameField.GIVEN: "Oliver",
                NameField.SURNAME: "{St John-Mollusc}",
            },
            "Nigel Incubator-Jones": {
                NameField.GIVEN: "Nigel",
                NameField.SURNAME: "Incubator-Jones",
            },
            "Incubator-Jones, Nigel": {
                NameField.GIVEN: "Nigel",
                NameField.SURNAME: "Incubator-Jones",
            },
            "Ludwig van Beethoven": {
                NameField.GIVEN: "Ludwig",
                "surname-prefix": "van",
                "surname-core": "Beethoven",
                NameField.SURNAME: "van Beethoven",
            },
            "van Beethoven, Ludwig": {
                NameField.GIVEN: "Ludwig",
                "surname-prefix": "van",
                "surname-core": "Beethoven",
                NameField.SURNAME: "van Beethoven",
            },
            "Charles Louis Xavier Joseph de la Vall{'e}e Poussin": {
                "surname-prefix": "de la",
                "surname-core": "Vall{'e}e Poussin",
                NameField.GIVEN: "Charles Louis Xavier Joseph",
                NameField.SURNAME: "de la Vall{'e}e Poussin",
            },
            "R. J. Van de Graaff": {
                NameField.GIVEN: "R. J. Van",
                "surname-prefix": "de",
                "surname-core": "Graaff",
                NameField.SURNAME: "de Graaff",
            },
            "Van de Graaff, R. J.": {
                NameField.GIVEN: "R. J.",
                NameField.SURNAME: "Van de Graaff",
            },
            "Doe, Jr., John": {
                NameField.GIVEN: "John",
                NameField.GENERATION: "Jr.",
                NameField.SURNAME: "Doe",
            },
            "John Doe, Jr.": {NameField.GIVEN: "Jr.", NameField.SURNAME: "John Doe"},
            "Gates III, William H.": {
                NameField.GIVEN: "William H.",
                NameField.SURNAME: "Gates III",
            },
            "William H. Gates III": {
                NameField.GIVEN: "William H. Gates",
                NameField.SURNAME: "III",
            },
            "William H. {Gates III}": {
                NameField.GIVEN: "William H.",
                NameField.SURNAME: "{Gates III}",
            },
            "{Foo, Bar and Sons}": {NameField.SURNAME: "{Foo, Bar and Sons}"},
        }
        for name, parts in cases.items():
            spn = SimplePersonName.parse_bibtex(name)
            spn2 = SimplePersonName(parts)  # type: ignore
            self.assertEqual(spn, spn2)

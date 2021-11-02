from pylo import Organization, Label, LabelType

AUTH_LABEL_HREF = "/orgs/49/labels/3327"
AUTH_LABEL_NAME = 'A-AUTH'

"""
            {
                "href": "/orgs/49/labels/3327",
                "key": "app",
                "value": "A-AUTH",
                "created_at": "2021-09-28T05:22:49.247Z",
                "updated_at": "2021-09-28T05:22:49.247Z",
                "created_by": {
                    "href": "/users/50"
                },
                "updated_by": {
                    "href": "/users/50"
                }
            },
"""


def test_create_label(mock_pce: Organization):
    label = mock_pce.LabelStore.create_label("R-TEST-LABEL", label_type='ROLE', href='/orgs/49/labels/12345')
    assert label is not None and type(label) is Label


def test_find_label_by_href(mock_pce: Organization):
    label = mock_pce.LabelStore.find_by_href_or_die(AUTH_LABEL_HREF)
    assert label and label.name == AUTH_LABEL_NAME


def test_find_label_by_name(mock_pce: Organization):
    label = mock_pce.LabelStore.find_by_name(AUTH_LABEL_NAME)
    assert label and label.href == AUTH_LABEL_HREF


def test_find_all_by_name(mock_pce: Organization):
    mock_pce.LabelStore.create_label("WEB", label_type='ROLE', href='/orgs/49/labels/12345')
    mock_pce.LabelStore.create_label("Web", label_type='ROLE', href='/orgs/49/labels/12346')
    mock_pce.LabelStore.create_label("web", label_type='ROLE', href='/orgs/49/labels/12347')
    labels = mock_pce.LabelStore.find_all_by_name('web')
    assert len(labels) == 3


def test_find_all_by_name_and_type(mock_pce: Organization):
    mock_pce.LabelStore.create_label("WEB", label_type='ROLE', href='/orgs/49/labels/12345')
    mock_pce.LabelStore.create_label("Web", label_type='ROLE', href='/orgs/49/labels/12346')
    mock_pce.LabelStore.create_label("web", label_type='ROLE', href='/orgs/49/labels/12347')
    labels = mock_pce.LabelStore.find_all_by_name('web', label_type=LabelType.ROLE)
    assert len(labels) == 3


def test_find_all_by_name_any_type(mock_pce: Organization):
    mock_pce.LabelStore.create_label("TEST", label_type=LabelType.ROLE, href='/orgs/49/labels/12345')
    mock_pce.LabelStore.create_label("TEST", label_type=LabelType.APP, href='/orgs/49/labels/12346')
    mock_pce.LabelStore.create_label("TEST", label_type=LabelType.ENV, href='/orgs/49/labels/12347')
    labels = mock_pce.LabelStore.find_all_by_name('test')
    assert len(labels) == 3

AUTH_LABEL_HREF = "/orgs/49/labels/3327"
AUTH_LABEL_NAME = 'A-AUTH'


def test_create_label(mock_pce):
    pass

def test_find_label_by_href(mock_pce):
    label = mock_pce.LabelStore.find_by_href_or_die(AUTH_LABEL_HREF)
    assert label and label.name == AUTH_LABEL_NAME

def test_find_label_by_name(mock_pce):
    label = mock_pce.LabelStore.find_by_name(AUTH_LABEL_NAME)
    assert label and label.href == AUTH_LABEL_HREF

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
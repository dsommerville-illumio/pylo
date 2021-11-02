import pytest


def test_create_virtual_service(mock_pce):
    """
    API design musings

    mock_pce.create_virtual_service(*args)  # shallow, overloaded interface

    mock_pce.api.create_virtual_service(*args)  # same issue as above, but solves passthrough from PCE to API layer

    /api/v2/policy_objects/.../ < POST
    mock_pce.api.virtual_service.create(*args)  # violating law of demeter, but follows API language

    mock_pce.api.create(VirtualService, *args)  # requires user to know about internal object types (not self-documenting)

    mock_pce.virtual_service_api.create(*args)  # shrinks surface area, but not as intuitive

    mock_pce.virtual_service.create(*args)  # follows API language, maybe just a worse version of #3?
    """
    pass

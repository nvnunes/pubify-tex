from importlib import resources

from pubify_tex import install_pubify_package, prepare


def test_install_pubify_package_copies_packaged_asset(tmp_path):
    installed_path = install_pubify_package(tmp_path)
    assert installed_path == tmp_path / "pubify.sty"
    assert installed_path.exists()

    packaged_text = resources.files("pubify_tex.assets").joinpath("pubify.sty").read_text()
    assert installed_path.read_text() == packaged_text


def test_install_pubify_package_is_idempotent(tmp_path):
    first_path = install_pubify_package(tmp_path)
    second_path = install_pubify_package(tmp_path)
    assert first_path == tmp_path / "pubify.sty"
    assert second_path == first_path


def test_prepare_writes_package_and_template(tmp_path):
    package_path, template_path = prepare(
        tmp_path,
        template={"textwidth_in": 7.0, "textheight_in": 9.0},
    )
    assert package_path == tmp_path / "pubify.sty"
    assert template_path == tmp_path / "pubify-template.tex"
    assert package_path.exists()
    assert template_path.exists()

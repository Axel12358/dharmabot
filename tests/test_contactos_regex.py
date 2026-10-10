"""Regex puras de extraccion de contactos (emails/telefonos/LinkedIn)."""

from core.contactos_empresas import _DESCARTE, _EMAIL, _LINKEDIN, _TEL


def test_email_basico():
    assert _EMAIL.findall("Contacto: info@empresa.com o ventas@empresa.es") == [
        "info@empresa.com",
        "ventas@empresa.es",
    ]


def test_email_falsos_positivos():
    # sin TLD, TLD de 1 char, texto plano — no deben capturarse
    assert not _EMAIL.search("escribe a user@domain sin punto")
    assert not _EMAIL.search("contacto en a@b.c aqui")
    assert _EMAIL.findall("no es email: foo@bar") == []


def test_descarte_artefactos_web():
    assert _DESCARTE.search("logo@w3.org")
    assert _DESCARTE.search("a@schema.org")
    assert _DESCARTE.search("x@cdn.example.com/logo.png")
    assert not _DESCARTE.search("info@empresa.com")


def test_telefonos():
    assert _TEL.findall("Tel +34 912 345 678 y 912345678") == ["+34 912 345 678", "912345678"]
    assert not _TEL.findall("año 2026")


def test_linkedin_empresa():
    # el regex no incluye la barra final del slug
    assert _LINKEDIN.findall("https://www.linkedin.com/company/acme-corp/") == [
        "https://www.linkedin.com/company/acme-corp"
    ]
    assert not _LINKEDIN.findall("https://facebook.com/acme")

"""Locally generated demonstration documents and a room illustration; no external assets."""

import struct, zlib


def room_png():
    width, height = 640, 420

    def color(x, y):
        if y > 320:
            return (169, 143, 110)
        if 60 < x < 220 and 55 < y < 260:
            return (
                (102, 140, 144)
                if x not in range(135, 145) and y not in range(150, 160)
                else (240, 237, 223)
            )
        if 290 < x < 590 and 245 < y < 345:
            return (104, 126, 104)
        if 315 < x < 565 and 215 < y < 280:
            return (135, 152, 127)
        if 260 < x < 275 and 170 < y < 330:
            return (96, 88, 71)
        if 235 < x < 300 and 150 < y < 195:
            return (220, 200, 155)
        if 40 < x < 65 and 285 < y < 360:
            return (152, 110, 86)
        if ((x - 52) / 30) ** 2 + ((y - 260) / 50) ** 2 < 1:
            return (94, 132, 84)
        return (225, 218, 199)

    raw = b"".join(
        b"\x00" + bytes(c for x in range(width) for c in color(x, y))
        for y in range(height)
    )

    def chunk(t, data):
        return (
            struct.pack("!I", len(data))
            + t
            + data
            + struct.pack("!I", zlib.crc32(t + data) & 0xFFFFFFFF)
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack("!2I5B", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def quotation_pdf(
    phase=1,
    title="Surface preparation and interior painting",
    amount="85000",
    duration=14,
):
    lines = [
        [
            "YEP - DEMONSTRATION QUOTATION",
            f"Phase {phase}: {title}",
            "Materials: primer, emulsion, masking and protection",
            "Labour: preparation, two finish coats and clean-up",
            f"Total: INR {float(amount):,.2f} | Estimated duration: {duration} days",
            "This PDF is demo data; official amounts are recorded in the app.",
        ],
        [
            "YEP - TERMS AND SCOPE",
            "Site: Demo apartment, Pune",
            "Includes preparation, application and quality review.",
            "Payments are verified offline by Admin.",
            "Changes to scope require a revised quotation.",
            "This is page 2 of a locally generated sample document.",
        ],
    ]
    objects = [
        b"<</Type /Catalog /Pages 2 0 R>>",
        b"<</Type /Pages /Kids [3 0 R 5 0 R] /Count 2>>",
    ]
    for page in lines:
        stream = (
            b"BT /F1 14 Tf 50 780 Td "
            + b" ".join(
                (
                    "("
                    + line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
                    + ") Tj 0 -35 Td"
                ).encode("latin-1", errors="replace")
                for line in page
            )
            + b" ET"
        )
        content_index = len(objects) + 2
        objects.append(
            f"<</Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources <</Font <</F1 7 0 R>>>> /Contents {content_index} 0 R>>".encode()
        )
        objects.append(
            b"<</Length "
            + str(len(stream)).encode()
            + b">>\nstream\n"
            + stream
            + b"\nendstream"
        )
    objects.append(b"<</Type /Font /Subtype /Type1 /BaseFont /Helvetica>>")
    result = b"%PDF-1.4\n"
    offsets = [0]
    for i, o in enumerate(objects, 1):
        offsets.append(len(result))
        result += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
    xref = len(result)
    result += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets[1:]:
        result += f"{off:010d} 00000 n \n".encode()
    result += f"trailer <</Size {len(objects) + 1} /Root 1 0 R>>\nstartxref\n{xref}\n%%EOF".encode()
    return result

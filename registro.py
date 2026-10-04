from playwright.sync_api import sync_playwright  # type: ignore
import random, string, time

URL = "https://xenpaid.com/register?ref=christopher12"  # pon tu URL real
CANTIDAD = 5
CLAVE = "Test1234"
PAIS = "Dominican Republic"

NOMBRE_BASE = "Carlos"
APELLIDO_BASE = "Andujar"

usados = set()


def rand(n=6):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def cambiar_letra(texto):
    """Cambia una letra al azar del texto por otra distinta (mantiene mayúscula inicial)."""
    letras = list(texto.lower())
    pos = random.randrange(len(letras))
    nueva = random.choice([c for c in string.ascii_lowercase if c != letras[pos]])
    letras[pos] = nueva
    return "".join(letras).capitalize()


def nombre_unico():
    """Genera 'Nombre Apellido' con una letra cambiada en cada uno, sin repetir."""
    while True:
        nombre = cambiar_letra(NOMBRE_BASE)
        apellido = cambiar_letra(APELLIDO_BASE)
        completo = f"{nombre} {apellido}"
        if completo not in usados:
            usados.add(completo)
            return completo


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False)

    for i in range(CANTIDAD):
        uid = rand()
        nombre_completo = nombre_unico()
        respuestas = []

        page = browser.new_page()
        # Tiempo máximo por defecto para cualquier acción (45 s)
        page.set_default_timeout(45000)

        # Escuchar respuestas desde el inicio
        page.on(
            "response",
            lambda r: respuestas.append((r.request.method, r.status, r.url))
            if r.request.method == "POST" else None,
        )

        # Esperar a que la página cargue por completo (hasta 60 s)
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_selector('input[placeholder="Your full name"]', timeout=30000)

        page.fill('input[placeholder="Your full name"]', nombre_completo)
        page.fill('input[placeholder*="rahul99"]', f"user{uid}")
        page.fill('input[placeholder="you@email.com"]', f"user{uid}@gmail.com")
        page.fill(
            'input[placeholder*="+84912345678"]',
            "+1809" + "".join(random.choices(string.digits, k=7)),
        )

        # País: abrir lista, escribir y elegir
        page.click("text=Select your country")
        page.keyboard.type(PAIS, delay=50)
        page.wait_for_timeout(1000)
        try:
            page.get_by_text(PAIS, exact=True).first.click(timeout=10000)
        except Exception:
            page.keyboard.press("Enter")

        page.fill('input[placeholder="Min 6 characters"]', CLAVE)
        page.fill('input[placeholder="Repeat your password"]', CLAVE)
        page.check('input[type="checkbox"]')

        page.click("text=Create Account")

        # Esperar la confirmación hasta 30 s (la página tarda 10-15 s)
        try:
            page.wait_for_selector(
                "text=/profile created|perfil creado|success|welcome/i",
                timeout=50000,
            )
            estado = "OK"
        except Exception:
            estado = "SIN CONFIRMACIÓN"

        page.screenshot(path=f"intento_{i+1}.png", full_page=True)
        print(f"Registro {i+1}/{CANTIDAD}: {nombre_completo} (user{uid}) -> {estado}")
        for m, s, u in respuestas:
            print(f"   {m} {s} {u}")

        errores = page.locator(
            "[class*=error], [class*=invalid], [role=alert]"
        ).all_inner_texts()
        if errores:
            print("   Errores en pantalla:", errores)

        page.close()
        time.sleep(1)

    browser.close()
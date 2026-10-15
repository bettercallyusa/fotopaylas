
import os
import threading
import requests

from kivy.app import App
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import NumericProperty
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, Line, PushMatrix, PopMatrix, Rotate
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.modalview import ModalView

SUPABASE_URL = "https://ijkfdezshbinducjpnat.supabase.co"
SUPABASE_KEY = "sb_publishable_44uuBHMEkE8zwiN8quebyw_7hEow1_J"

BG = "#101014"
PANEL = "#1B1B23"
PANEL2 = "#252530"
WHITE = "#F5F5FA"
MUTED = "#A1A1B2"
PINK = "#E94D91"
PURPLE = "#8957E5"
GREEN = "#45C49A"
RED = "#FF667A"


def color(value):
    return get_color_from_hex(value)


def label(text, size=15, tint=WHITE, **kwargs):
    return Label(
        text=text,
        font_size=dp(size),
        color=color(tint),
        **kwargs
    )


def button(text, callback, bg=PANEL2, fg=WHITE, height=48):
    b = Button(
        text=text,
        size_hint_y=None,
        height=dp(height),
        background_normal="",
        background_down="",
        background_color=color(bg),
        color=color(fg),
        font_size=dp(15),
        bold=True
    )
    b.bind(on_release=lambda *_: callback())
    return b


def field(hint, password=False):
    return TextInput(
        hint_text=hint,
        password=password,
        multiline=False,
        size_hint_y=None,
        height=dp(50),
        padding=[dp(14), dp(14), dp(14), dp(10)],
        background_normal="",
        background_active="",
        background_color=color(PANEL2),
        foreground_color=color(WHITE),
        hint_text_color=color(MUTED),
        cursor_color=color(PINK),
        font_size=dp(15)
    )


class RotatingLoader(Widget):
    angle = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            PushMatrix()
            self.rotation = Rotate(angle=0, origin=self.center)
            Color(*color(PINK))
            self.ring = Line(
                circle=(self.center_x, self.center_y, dp(22), 35, 310),
                width=dp(3.5),
                cap="round"
            )
            PopMatrix()

        self.bind(pos=self.redraw, size=self.redraw, angle=self.redraw)

    def redraw(self, *_):
        self.rotation.origin = self.center
        self.rotation.angle = self.angle
        self.ring.circle = (
            self.center_x, self.center_y, dp(22), 35, 310
        )


class LoadingPopup(ModalView):
    def __init__(self, message="İşlem yapılıyor...", **kwargs):
        super().__init__(
            size_hint=(1, 1),
            background_color=(0, 0, 0, 0.60),
            background="",
            auto_dismiss=False,
            **kwargs
        )
        panel = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            size=(dp(220), dp(175)),
            spacing=dp(10),
            padding=dp(18)
        )
        with panel.canvas.before:
            Color(*color(PANEL))
            from kivy.graphics import RoundedRectangle
            self.panel_bg = RoundedRectangle(
                pos=panel.pos, size=panel.size, radius=[dp(20)]
            )
        panel.bind(
            pos=lambda w, *_: setattr(self.panel_bg, "pos", w.pos),
            size=lambda w, *_: setattr(self.panel_bg, "size", w.size)
        )

        self.loader = RotatingLoader(size_hint=(None, None),
                                     size=(dp(56), dp(56)))
        panel.add_widget(self.loader)
        panel.add_widget(label(message, 14, WHITE))
        self.add_widget(panel)

        panel.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        self.anim = Animation(angle=360, duration=0.8)
        self.anim.repeat = True

    def on_open(self):
        self.anim.start(self.loader)

    def on_dismiss(self):
        self.anim.cancel(self.loader)


class BaseScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()

    def page(self, title, subtitle=None):
        root = BoxLayout(
            orientation="vertical",
            padding=[dp(18), dp(16), dp(18), dp(12)],
            spacing=dp(12)
        )
        with root.canvas.before:
            Color(*color(BG))
            self.bg_rect = __import__(
                "kivy.graphics", fromlist=["Rectangle"]
            ).Rectangle(pos=root.pos, size=root.size)
        root.bind(
            pos=lambda w, *_: setattr(self.bg_rect, "pos", w.pos),
            size=lambda w, *_: setattr(self.bg_rect, "size", w.size)
        )

        head = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(62),
            spacing=dp(3)
        )
        head.add_widget(label(title, 25, WHITE, bold=True,
                              halign="left", valign="middle"))
        if subtitle:
            head.add_widget(label(subtitle, 12, MUTED, halign="left"))
        root.add_widget(head)
        return root

    def card(self, padding=14, spacing=8):
        box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=dp(padding),
            spacing=dp(spacing)
        )
        box.bind(minimum_height=box.setter("height"))
        with box.canvas.before:
            Color(*color(PANEL))
            from kivy.graphics import RoundedRectangle
            box.bg_rect = RoundedRectangle(
                pos=box.pos, size=box.size, radius=[dp(18)]
            )
        box.bind(
            pos=lambda w, *_: setattr(w.bg_rect, "pos", w.pos),
            size=lambda w, *_: setattr(w.bg_rect, "size", w.size)
        )
        return box


class AuthScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_mode = False
        self.root_box = self.page(
            "FotoPaylaş",
            "Fotoğraflarını paylaş, anılarını biriktir."
        )

        brand = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(110),
            spacing=dp(5)
        )
        brand.add_widget(label("●", 43, PINK))
        brand.add_widget(label("Anlarını paylaş.", 21, WHITE, bold=True))
        brand.add_widget(label(
            "Yeni insanlarla bağlantı kur.", 13, MUTED
        ))
        self.root_box.add_widget(brand)

        self.form = self.card(18, 12)
        self.mode_title = label("Hoş geldin", 21, WHITE, bold=True,
                                halign="left")
        self.form.add_widget(self.mode_title)

        self.email = field("E-posta adresin")
        self.password = field("Şifren", True)
        self.form.add_widget(self.email)
        self.form.add_widget(self.password)

        self.confirm = field("Şifreni tekrar gir", True)
        self.form.add_widget(self.confirm)
        self.confirm.height = dp(0)
        self.confirm.opacity = 0
        self.confirm.disabled = True

        self.action = button("Giriş yap", self.submit, PINK)
        self.form.add_widget(self.action)

        self.mode_button = button(
            "Hesabın yok mu? Kayıt ol",
            self.toggle_mode, PANEL2, WHITE, 44
        )
        self.form.add_widget(self.mode_button)
        self.root_box.add_widget(self.form)
        self.root_box.add_widget(Widget())
        self.add_widget(self.root_box)
        self.set_mode(False)

    def set_mode(self, register):
        self.register_mode = register
        self.mode_title.text = "Hesap oluştur" if register else "Hoş geldin"
        self.action.text = "Kayıt ol" if register else "Giriş yap"
        self.mode_button.text = (
            "Zaten hesabın var mı? Giriş yap"
            if register else "Hesabın yok mu? Kayıt ol"
        )
        self.confirm.height = dp(50) if register else 0
        self.confirm.opacity = 1 if register else 0
        self.confirm.disabled = not register
        self.confirm.text = ""

    def toggle_mode(self):
        self.set_mode(not self.register_mode)

    def submit(self):
        email = self.email.text.strip()
        password = self.password.text

        if not email or not password:
            self.app.notice("E-posta ve şifre alanlarını doldur.")
            return

        if self.register_mode:
            if password != self.confirm.text:
                self.app.notice("Şifreler birbiriyle aynı değil.")
                return
            if len(password) < 6:
                self.app.notice("Şifren en az 6 karakter olmalı.")
                return

        self.app.run_network(
            "Hesabın kontrol ediliyor...",
            self.auth_request,
            email,
            password,
            self.register_mode
        )

    def auth_request(self, email, password, register):
        headers = {
            "apikey": SUPABASE_KEY,
            "Content-Type": "application/json"
        }
        if register:
            url = SUPABASE_URL + "/auth/v1/signup"
        else:
            url = SUPABASE_URL + "/auth/v1/token?grant_type=password"

        response = requests.post(
            url,
            headers=headers,
            json={"email": email, "password": password},
            timeout=25
        )
        data = response.json()

        if response.status_code not in (200, 201):
            msg = data.get("msg") or data.get("message")
            if not msg and isinstance(data.get("error"), str):
                msg = data["error"]
            if not msg:
                msg = data.get("error_description", "İşlem başarısız.")
            raise Exception(str(msg))

        if not register and not data.get("access_token"):
            raise Exception("Giriş tamamlanamadı. Bilgilerini kontrol et.")

        if not register:
            self.app.access_token = data["access_token"]
            self.app.user = data.get("user", {})
        return ("register" if register else "login", data)

    def auth_success(self, result):
        kind, data = result
        if kind == "register":
            if data.get("access_token"):
                self.app.access_token = data["access_token"]
                self.app.user = data.get("user", {})
                self.app.show_home()
            else:
                self.app.notice(
                    "Kayıt oluşturuldu. Şimdi giriş yapabilirsin."
                )
                self.set_mode(False)
        else:
            self.app.show_home()


class HomeScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = self.page("FotoPaylaş", "Günlük anlar, gerçek bağlantılar")
        scroll = __import__(
            "kivy.uix.scrollview", fromlist=["ScrollView"]
        ).ScrollView(do_scroll_x=False)

        content = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=dp(14)
        )
        content.bind(minimum_height=content.setter("height"))

        stories = self.card(12, 10)
        stories.add_widget(label("HİKÂYELER", 12, MUTED, halign="left"))
        story_row = GridLayout(
            cols=4, size_hint_y=None, height=dp(92), spacing=dp(6)
        )
        for symbol, name, tint in [
            ("＋", "Sen", PINK), ("●", "Keşfet", PURPLE),
            ("●", "Anlar", GREEN), ("●", "Dostlar", "#EAA45A")
        ]:
            tile = BoxLayout(orientation="vertical", spacing=dp(4))
            tile.add_widget(label(symbol, 29, tint))
            tile.add_widget(label(name, 11, MUTED))
            story_row.add_widget(tile)
        stories.add_widget(story_row)
        content.add_widget(stories)

        content.add_widget(label("Senin için", 20, WHITE, bold=True,
                                 halign="left"))

        post = self.card(0, 10)
        post.add_widget(label("●   FotoPaylaş topluluğu", 14, WHITE,
                              halign="left"))
        image_area = BoxLayout(
            size_hint_y=None, height=dp(225),
            orientation="vertical", padding=dp(12)
        )
        with image_area.canvas.before:
            Color(*color("#302344"))
            from kivy.graphics import RoundedRectangle
            image_area.rect = RoundedRectangle(
                pos=image_area.pos, size=image_area.size, radius=[dp(16)]
            )
        image_area.bind(
            pos=lambda w, *_: setattr(w.rect, "pos", w.pos),
            size=lambda w, *_: setattr(w.rect, "size", w.size)
        )
        image_area.add_widget(label("✦", 52, "#F1B4E0"))
        image_area.add_widget(label(
            "Her güzel an bir hikâyedir.", 15, WHITE
        ))
        post.add_widget(image_area)
        post.add_widget(label("♡     Beğen       ◯   Yorum", 16, WHITE,
                              halign="left"))
        post.add_widget(label(
            "İlk paylaşımını yapmak için fotoğraf ekle.", 13, MUTED,
            halign="left"
        ))
        post.add_widget(button(
            "＋  Fotoğraf ekle",
            lambda: self.app.notice(
                "Fotoğraf seçiciyi bir sonraki adımda düzelteceğiz."
            ),
            PANEL2, WHITE, 44
        ))
        content.add_widget(post)

        scroll.add_widget(content)
        root.add_widget(scroll)
        root.add_widget(self.nav("home"))
        self.add_widget(root)

    def nav(self, active):
        bar = GridLayout(
            cols=4, size_hint_y=None, height=dp(55), spacing=dp(6)
        )
        items = [
            ("⌂\nAna sayfa", "home", self.app.show_home),
            ("⌕\nKeşfet", "discover", self.app.show_discover),
            ("＋\nPaylaş", "share", self.app.show_share),
            ("◉\nProfil", "profile", self.app.show_profile)
        ]
        for text, name, callback in items:
            bar.add_widget(button(
                text, callback, PINK if name == active else PANEL,
                WHITE, 52
            ))
        return bar


class DiscoverScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = self.page("Keşfet", "Yeni şeyler keşfet")
        root.add_widget(self.card())
        root.children[0].add_widget(label(
            "Henüz keşfedilecek gönderi yok.", 15, MUTED
        ))
        root.add_widget(Widget())
        root.add_widget(self.nav("discover"))
        self.add_widget(root)

    def nav(self, active):
        return HomeScreenNav(self.app, active)


class HomeScreenNav(GridLayout):
    def __init__(self, app, active, **kwargs):
        super().__init__(cols=4, size_hint_y=None,
                         height=dp(55), spacing=dp(6), **kwargs)
        for text, name, callback in [
            ("⌂\nAna sayfa", "home", app.show_home),
            ("⌕\nKeşfet", "discover", app.show_discover),
            ("＋\nPaylaş", "share", app.show_share),
            ("◉\nProfil", "profile", app.show_profile)
        ]:
            self.add_widget(button(
                text, callback, PINK if name == active else PANEL,
                WHITE, 52
            ))


class ProfileScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root_box = self.page("Profil", "Hesabın ve paylaşımların")
        self.info = self.card(18, 10)
        self.info.add_widget(label("◉", 48, PINK))
        self.email_label = label("", 16, WHITE, bold=True)
        self.info.add_widget(self.email_label)
        self.info.add_widget(label("0 paylaşım", 13, MUTED))
        self.root_box.add_widget(self.info)
        self.root_box.add_widget(button(
            "＋  Fotoğraf paylaş",
            lambda: self.app.show_share(), PINK
        ))
        self.root_box.add_widget(button(
            "Çıkış yap", self.app.logout, PANEL2, WHITE
        ))
        self.root_box.add_widget(Widget())
        self.root_box.add_widget(HomeScreenNav(self.app, "profile"))
        self.add_widget(self.root_box)

    def on_pre_enter(self, *_):
        user = self.app.user or {}
        self.email_label.text = user.get("email", "FotoPaylaş kullanıcısı")


class ShareScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = self.page("Yeni paylaşım", "Bir anını paylaş")
        card = self.card(18, 12)
        card.add_widget(label("Fotoğrafını seç", 19, WHITE, bold=True))
        card.add_widget(label(
            "Fotoğraf seçme desteğini güvenilir dosya seçiciyle "
            "bir sonraki adımda bağlayacağız.", 13, MUTED
        ))
        card.add_widget(button(
            "Fotoğraf seç", self.pick_photo, PINK
        ))
        root.add_widget(card)
        root.add_widget(Widget())
        root.add_widget(HomeScreenNav(self.app, "share"))
        self.add_widget(root)

    def pick_photo(self):
        self.app.notice(
            "Dosya seçiciyi bu sürümde açmıyoruz; X11'in takılmasını önlüyoruz."
        )


class FotoPaylasApp(App):
    access_token = None
    user = None

    def build(self):
        self.title = "FotoPaylaş"
        self.sm = ScreenManager()
        self.sm.add_widget(AuthScreen(name="auth"))
        self.sm.add_widget(HomeScreen(name="home"))
        self.sm.add_widget(DiscoverScreen(name="discover"))
        self.sm.add_widget(ShareScreen(name="share"))
        self.sm.add_widget(ProfileScreen(name="profile"))
        self.loading = None
        self.notice_popup = None
        return self.sm

    def notice(self, message):
        if self.notice_popup:
            try:
                self.notice_popup.dismiss()
            except Exception:
                pass

        popup = ModalView(
            size_hint=(0.88, None),
            height=dp(150),
            auto_dismiss=True,
            background="",
            background_color=(0, 0, 0, 0.35)
        )
        box = BoxLayout(
            orientation="vertical", padding=dp(18), spacing=dp(12)
        )
        with box.canvas.before:
            Color(*color(PANEL))
            from kivy.graphics import RoundedRectangle
            rect = RoundedRectangle(
                pos=box.pos, size=box.size, radius=[dp(18)]
            )
        box.bind(
            pos=lambda w, *_: setattr(rect, "pos", w.pos),
            size=lambda w, *_: setattr(rect, "size", w.size)
        )
        box.add_widget(label(message, 14, WHITE))
        b = button("Tamam", popup.dismiss, PINK, WHITE, 42)
        box.add_widget(b)
        popup.add_widget(box)
        self.notice_popup = popup
        popup.open()

    def run_network(self, message, worker, *args):
        if self.loading:
            return

        self.loading = LoadingPopup(message)
        self.loading.open()

        def run():
            try:
                result = worker(*args)
                Clock.schedule_once(
                    lambda dt: self.network_done(result=result), 0
                )
            except Exception as exc:
                Clock.schedule_once(
                    lambda dt, e=str(exc): self.network_done(error=e), 0
                )

        threading.Thread(target=run, daemon=True).start()

    def network_done(self, result=None, error=None):
        if self.loading:
            self.loading.dismiss()
            self.loading = None

        if error:
            self.notice("İşlem başarısız:\n" + error)
            return

        screen = self.sm.get_screen("auth")
        screen.auth_success(result)

    def show_home(self):
        self.sm.current = "home"

    def show_discover(self):
        self.sm.current = "discover"

    def show_share(self):
        self.sm.current = "share"

    def show_profile(self):
        self.sm.current = "profile"

    def logout(self):
        self.access_token = None
        self.user = None
        self.sm.current = "auth"


if __name__ == "__main__":
    FotoPaylasApp().run()

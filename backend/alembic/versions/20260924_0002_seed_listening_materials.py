"""seed baseline listening and speaking practice materials

Revision ID: 20260924_0002
Revises: 20260924_0001
Create Date: 2026-09-24
"""

from alembic import op


revision = "20260924_0002"
down_revision = "20260924_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Empty audio_url intentionally selects the browser's de-DE speech
    # synthesis fallback until licensed recordings are uploaded.
    op.execute(
        """
        INSERT INTO listening_materials (title, level, duration, audio_url, script)
        VALUES
            (
                'Begrüßungen im Alltag', 'A1', '0:35', '',
                'Hallo! Guten Morgen! Wie geht es Ihnen? Mir geht es gut, danke. Und Ihnen? Auch gut, danke der Nachfrage. Auf Wiedersehen!'
            ),
            (
                'Im Café bestellen', 'A1', '0:45', '',
                'Guten Tag! Ich hätte gern einen Kaffee und ein Stück Apfelkuchen, bitte. Möchten Sie den Kaffee mit Milch? Ja, gern. Das macht sechs Euro zwanzig.'
            ),
            (
                'Am Bahnhof', 'A2', '0:50', '',
                'Entschuldigung, wann fährt der nächste Zug nach München? Der Zug fährt um vierzehn Uhr dreißig von Gleis fünf. Muss ich umsteigen? Nein, es ist eine Direktverbindung.'
            ),
            (
                'Beim Arzt', 'A2', '0:55', '',
                'Was kann ich für Sie tun? Ich habe seit gestern Abend Kopfschmerzen und Fieber. Haben Sie auch Halsschmerzen? Ja, ein bisschen. Ich verschreibe Ihnen ein Medikament.'
            ),
            (
                'Eine Wohnung besichtigen', 'B1', '1:05', '',
                'Die Wohnung liegt im dritten Stock und hat drei Zimmer, eine Küche und einen Balkon. Die Warmmiete beträgt neunhundertfünfzig Euro. Einkaufsmöglichkeiten und die U-Bahn sind nur wenige Minuten entfernt. Die Wohnung ist ab dem ersten Oktober frei.'
            ),
            (
                'Besprechung im Büro', 'B2', '1:15', '',
                'Bevor wir mit der Umsetzung beginnen, sollten wir die Rückmeldungen unserer Kundinnen und Kunden genauer auswerten. Besonders wichtig sind eine verständliche Navigation und kürzere Ladezeiten. Ich schlage vor, dass wir die Aufgaben priorisieren und am Freitag einen realistischen Zeitplan verabschieden.'
            )
        ON CONFLICT (title) DO UPDATE SET
            level = EXCLUDED.level,
            duration = EXCLUDED.duration,
            script = EXCLUDED.script
        """
    )


def downgrade() -> None:
    # Learning records may already reference these rows; keep downgrade
    # non-destructive rather than deleting user-linked practice material.
    pass

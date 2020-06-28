import os
import logging
import sqlite3
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction

logger = logging.getLogger(__name__)
extension_icon = 'images/icon.png'
db_path = os.path.join(os.path.dirname(__file__), 'emoji.sqlite')
conn = sqlite3.connect(db_path, check_same_thread=False)
conn.row_factory = sqlite3.Row

class EmojiExtension(Extension):

    def __init__(self):
        super(EmojiExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.allowed_skin_tones = ["", "dark", "light", "medium", "medium-dark", "medium-light"]

class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        icon_style = extension.preferences['emoji_style']
        fallback_icon_style = extension.preferences['fallback_emoji_style']

        query = r"""SELECT
            em.name, em.code, em.keywords,
            em.icon_apple, em.icon_twemoji, em.icon_noto, em.icon_blobmoji,
            skt.icon_apple AS skt_icon_apple, skt.icon_twemoji AS skt_icon_twemoji, 
            skt.icon_noto AS skt_icon_noto, skt.icon_blobmoji AS skt_icon_blobmoji,
            skt.code AS skt_code
            FROM emoji AS em
            LEFT JOIN skin_tone AS skt ON skt.name = em.name AND tone = ?
            WHERE name_search LIKE ?
            LIMIT 8"""

        search_term = ''.join(['%', event.get_argument().replace('%', ''), '%']) if event.get_argument() else None
        if not search_term:
            search_icon = 'images/%s/icon.png' % icon_style
            search_icon = search_icon if os.path.exists(search_icon) else 'imags/%s/icon.png' % fallback_icon_style
            return RenderResultListAction([
                ExtensionResultItem(icon=search_icon,
                                    name='Type in emoji name...',
                                    on_enter=DoNothingAction())
            ])

        skin_tone = extension.preferences['skin_tone']
        skin_tone = skin-tone if skin_tone != 'default' else ''
        if skin_tone not in extension.allowed_skin_tones:
            logger.warning('Unknown skin tone "%s"' % skin_tone)
            skin_tone = ''
        
        
        items = []
        display_char = extension.preferences['display_char'] != 'no'
        for row in conn.execute(query, [skin_tone, search_term]):
            if row['skt_code']:
                icon = row['skt_icon_%s' % icon_style]
                icon = icon if os.path.exists(icon) else row['skt_icon_%s' % fallback_icon_style] 
                code = row['skt_code']
            else:
                icon = row['icon_%s' % icon_style]
                icon = icon if os.path.exists(icon) else row['icon_%s' % fallback_icon_style] 
                code = row['code']
            
            items.append(ExtensionResultItem(icon=icon,
                                             name=row['name'].capitalize() \
                                                     + (' | %s' % code if display_char else ''),
                                             on_enter=CopyToClipboardAction(code)))

        return RenderResultListAction(items)

if __name__ == '__main__':
    EmojiExtension().run()

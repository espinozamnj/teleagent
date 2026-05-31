import datetime
from telegram import Update
from telegram.ext import ContextTypes

from teleagent.core import state
from teleagent.utils.helpers import log_history
from teleagent.handlers.messages import _execute_and_reply

async def handle_confirmation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if user_id not in state.AUTHORIZED_USERS or user_id not in state.PENDING_CONFIRMATIONS:
        await query.edit_message_reply_markup(reply_markup=None)
        return

    data = state.PENDING_CONFIRMATIONS.pop(user_id)
    elapsed = (datetime.datetime.now() - data['sent_at']).total_seconds()

    if elapsed > state.LAST_MINUTE_TIMEOUT:
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(f"⚠️ Command ignored: expired after {state.LAST_MINUTE_TIMEOUT}s.")
        log_history(query.message.chat_id, data['raw_message'], data['target_user'], data['expanded_msg'], "%")
        return

    if query.data == 'lm_cancel':
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("❌ Confirmation cancelled.")
        log_history(query.message.chat_id, data['raw_message'], data['target_user'], data['expanded_msg'], "%")
        return

    await query.edit_message_reply_markup(reply_markup=None)
    await _execute_and_reply(
        data['msg_obj'],
        data['raw_message'],
        data['target_user'],
        data['command'],
        data['expanded_msg'],
        data.get('paths', [])
    )

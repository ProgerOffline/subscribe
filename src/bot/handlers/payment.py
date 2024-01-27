from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from data.config import SUBSCRIBE_AMOUNT_BY_PLANS, USDT_TRC20_WALLET_ADDRESS
from database import transactions
from keyboards import inline as inline_keyboards
from statesgroup import GetTxidFromUser
from utils import tronscan_service

payment_router = Router()


@payment_router.callback_query(F.data == "make_subscription")
async def make_subscription(call: types.CallbackQuery):
    if call.message is None:
        return
    await call.message.edit_text(
        text=f"Choose subscription plan",
        reply_markup=await inline_keyboards.subscription_termins(
            SUBSCRIBE_AMOUNT_BY_PLANS.keys()
        ),
    )


@payment_router.callback_query(F.data.contains("month"))
async def set_subscribtion_termin(call: types.CallbackQuery, state: FSMContext):
    if call.data is None:
        return
    termin = int(call.data.split("_")[1])
    await state.set_data({"subscription_termin": termin})
    if call.message is None:
        return
    await call.message.answer(
        text=f"To pay, use this <code>USDT TC20</code> wallet: <code>{USDT_TRC20_WALLET_ADDRESS}</code>.\n"
        f"Transfer {SUBSCRIBE_AMOUNT_BY_PLANS[termin]} <code>USDT TRC20</code>.\n"
        "After submitting, click the Confirm button.",
        reply_markup=await inline_keyboards.confirm_transfer(),
    )


@payment_router.callback_query(F.data == "confirm_transfer")
async def confirm_transfer(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(GetTxidFromUser.state)
    if call.message is None:
        return
    await call.message.answer(
        text="Great, send me the transaction txid to verify the transfer.",
        reply_markup=types.ReplyKeyboardRemove(),
    )


@payment_router.message(GetTxidFromUser.state)
async def check_transaction(message: types.Message, state: FSMContext):
    transaction = await transactions.get(txid=message.text)

    if message.text is None or message.from_user is None:
        return

    if transaction is None and tronscan_service.is_valid_transaction_hash(message.text):
        data = await state.get_data()
        await transactions.create(
            message.text,
            message.from_user.id,
            data["subscription_termin"],
        )
        await state.clear()
        await message.answer(
            text="Great, wait for the end of the transaction, "
            "and I will notify you when the subscription is charged.",
            reply_markup=await inline_keyboards.back_to_main_menu(),
        )
    else:
        await message.answer(
            text="Please send me a new transaction, or check the txid",
        )

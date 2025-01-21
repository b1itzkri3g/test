import asyncio
import logging
import sys
from os import getenv
from aiogram import F
from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import *
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton,ReplyKeyboardMarkup,KeyboardButton,BotCommand
from aiogram.utils.keyboard import InlineKeyboardBuilder,ReplyKeyboardBuilder
from aiogram.filters.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from database import DatabaseManager
from loader import db,dp,bot
import smile_one
import smile_one_ph
from datetime import datetime,timedelta
import json
import re
from aiogram.types import FSInputFile
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from fpdf import FPDF
import unicodedata
from aiogram.types import InputFile
import io
from tempfile import gettempdir
import os
from aiogram.fsm.context import FSMContext
from aiogram.filters.callback_data import CallbackData



# Function to sanitize text to latin-1 compatible
def sanitize_to_latin1(text):
    return ''.join(
        char if char in ''.join(chr(i) for i in range(256)) else '?' for char in text
    )

class PDF(FPDF):
    def header(self):
        # Add logo
        self.image("lhp_logo.jpg", 10, 8, 33)  # Adjust the file path and dimensions as needed
        self.set_font("Arial", style="B", size=14)
        self.cell(0, 10, "LHP Game Store - Diamond Price List", align="C", ln=True)
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", size=8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

    def add_table(self, headers, data, col_widths):
        self.set_font("Arial", size=10)

        # Table header
        self.set_fill_color(100, 149, 237)  # Cornflower blue
        self.set_text_color(255)  # White text for the header
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 10, header, border=1, align="C", fill=True)
        self.ln()

        # Table rows
        self.set_text_color(0)  # Reset text color
        self.set_fill_color(240, 240, 240)  # Light gray for alternating rows
        for idx, row in enumerate(data):
            fill = idx % 2 == 0  # Alternate row fill
            for i, cell in enumerate(row):
                self.cell(col_widths[i], 10, str(cell), border=1, align="C", fill=fill)
            self.ln()

@dp.message(F.text==".noti")
async def send_welcome(message: types.Message):
    uid = db.fetchall('SELECT * FROM users')
    for u in uid:
        u_id = int(u[0])
        await bot.send_message(u_id,"hello")
    

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    builder = InlineKeyboardBuilder()

    builder.button(text=f"Login", callback_data=f"login")
    builder.button(text=f"Getid", callback_data=f"getid")
    builder.button(text=f"Help", callback_data=f"help")
    await message.answer(f"Hello, {hbold(message.from_user.full_name)}!",reply_markup=builder.as_markup())

@dp.callback_query(lambda c: c.data == 'getid')
async def process_getid_click(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await callback_query.message.answer(f"Your user ID is: {user_id}")


@dp.callback_query(lambda c: c.data == 'help')
async def process_getid_click(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await callback_query.message.answer(f"Contact to an Admin")


class Form(StatesGroup):
    username = State()
    password = State()
    session = State()

credential = []


@dp.callback_query(lambda c: c.data == 'login')
async def process_login_click(callback_query: types.CallbackQuery,state: FSMContext)-> None:
    user_id = callback_query.from_user.id
    udx = db.fetchone('SELECT * FROM users WHERE user_id=?', (user_id,))
    if udx is not None:
        await state.set_state(Form.username)
        await callback_query.message.answer("Please enter your username: ")
    else:
        await callback_query.message.answer(f"You are not register. use /start to see menu")

@dp.message(Form.username)
async def get_username(message: types.Message,state: FSMContext)-> None:
    global credential
    user_id = message.from_user.id
    username = message.text
    credential.append(username)
    await state.set_state(Form.password)
    await message.answer("Please enter your password:")


@dp.message(Form.password)
async def get_username(message: types.Message,state: FSMContext)-> None:

    global credential
    user_id = message.from_user.id
    password = message.text
    credential.append(password)
    username_db = db.fetchone('SELECT username FROM users WHERE user_id=?', (user_id,))
    password_db = db.fetchone('SELECT password FROM users WHERE user_id=?', (user_id,))
    username_db = ''.join(username_db)
    password_db = ''.join(password_db)
    if credential[0] == username_db and credential[1] == password_db:
        credential = []
        await show_menu(message) 
        await state.set_state(Form.session)
    else:
        credential = []
        await message.answer('Login failed')
        await state.clear()

# Define a custom CallbackData subclass
class PaginationCallback(CallbackData, prefix="pagination"):
    page: int

@dp.message(F.text == ".history")
async def history(message: types.Message, state: FSMContext) -> None:
    main_user = message.from_user.id
    my_tran = db.fetchall('SELECT * FROM transcation WHERE main_user=?', (main_user,))

    if my_tran:
        await send_paginated_history(message, my_tran, page=1)
    else:
        await message.answer("You have no transaction history.")

async def send_paginated_history(message: types.Message, transactions: list, page: int) -> None:
    per_page = 10  # Number of transactions per page
    total_pages = -(-len(transactions) // per_page)  # Ceiling division to calculate total pages

    # Get transactions for the current page
    start = (page - 1) * per_page
    end = start + per_page
    transactions_page = transactions[start:end]

    # Build the message
    history_message = f"Transaction History (Page {page}/{total_pages}):\n\n"
    for tran in transactions_page:
        history_message += f"Transaction ID: {tran[0]}\n"
        history_message += f"Details: {tran[1]}\n"
        history_message += f"Amount: {tran[2]}\n"
        history_message += f"Date: {tran[3]}\n"
        history_message += f"Status: {tran[4]}\n"
        history_message += "--------------------------------\n"

    # Add navigation buttons
    buttons = []
    if page > 1:
        buttons.append(types.InlineKeyboardButton(
            text="⬅️ Previous", 
            callback_data=PaginationCallback(page=page - 1).pack()
        ))
    if page < total_pages:
        buttons.append(types.InlineKeyboardButton(
            text="Next ➡️", 
            callback_data=PaginationCallback(page=page + 1).pack()
        ))

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[buttons])

    await message.answer(history_message, reply_markup=keyboard)

@dp.callback_query(PaginationCallback.filter())
async def pagination_callback(query: types.CallbackQuery, callback_data: PaginationCallback) -> None:
    page = callback_data.page
    main_user = query.from_user.id
    my_tran = db.fetchall('SELECT * FROM transcation WHERE main_user=?', (main_user,))

    # Edit the message with the requested page
    await query.message.edit_text(text="Loading...", reply_markup=None)
    await send_paginated_history(query.message, my_tran, page=page)
    await query.answer()



@dp.message(F.text==".price_list")
async def pricelist(message: types.Message, state: FSMContext) -> None:
    # Fetch data from the database
    pri = db.fetchall('SELECT * FROM dia_price')
    pri_ph = db.fetchall('SELECT * FROM dia_price_ph')

    # Prepare data for tables
    headers = ["#", "Diamonds", "Coins"]
    region1_data = [[idx + 1, item[1], item[2]] for idx, item in enumerate(pri)]
    region2_data = [[idx + 1, item[1], item[2]] for idx, item in enumerate(pri_ph)]

    # Generate a price list PDF
    pdf = PDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Add Region 1 Table
    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(0, 10, "Diamond Price List (Brazil Region)", ln=True)
    pdf.ln(5)
    pdf.add_table(headers, region1_data, [10, 80, 50])

    pdf.ln(10)

    # Add Region 2 Table
    pdf.cell(0, 10, "Diamond Price List (Philippines Region)", ln=True)
    pdf.ln(5)
    pdf.add_table(headers, region2_data, [10, 80, 50])

    # Save the PDF to a file
    pdf_file_path = "price_list.pdf"
    pdf.output(pdf_file_path)

    # Send the PDF file
    await message.answer_document(FSInputFile(pdf_file_path))

    # Inline menu
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏷 Check smileone.com Pricelist", url="https://www.smile.one/")],
        [InlineKeyboardButton(text="🏠 Back to Menu", callback_data="back_to_menu")],
    ])
    await message.answer(
        "🎉 Explore the website for more options or return to the main menu:",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu_callback(callback_query: types.CallbackQuery) -> None:
    # Handle redirection to the menu
    await callback_query.message.answer("📋 Returning to the main menu...")

    # Access the bot instance directly from the bot object
    await show_menu(callback_query.message)  # Pass the message to show_menu

    await callback_query.answer()  # Acknowledge the callback




async def send_beautified_voucher(message, tran_id, diamond, actual_wp, userid, zoneid, username, status, coin_value, my_bal, formatted_date):
    beautified_text = (
        f"<b>🎟️ Payment Voucher</b>\n"
        f"<b>====================</b>\n\n"
        f"<b>📜 Transaction ID:</b> {hbold(tran_id)}\n"
        f"<b>💎 Product:</b> {hbold(diamond)} Diamonds\n"
        f"<b>✅ Successful WP:</b> {hbold(actual_wp)}\n"
        f"<b>👤 User ID:</b> {hbold(userid)}\n"
        f"<b>🆔 Zone ID:</b> {hbold(zoneid)}\n"
        f"<b>🌐 Username:</b> {hbold(username)}\n"
        f"<b>📊 Status:</b> {hbold(status)}\n\n"
        f"<b>💰 Debited from Balance:</b> ${hbold(coin_value)}\n"
        f"<b>📉 Remaining Balance:</b> ${hbold(my_bal)}\n\n"
        f"<i>🗓️ Date:</i> {hitalic(formatted_date)}\n"
        f"<b>====================</b>"
    )
    
    # Send beautified voucher text with HTML formatting
    await message.answer(beautified_text, parse_mode="HTML")





def remove_unsupported_characters(text):
    """Remove unsupported characters for FPDF (supports only Latin-1)."""
    return re.sub(r'[^\x20-\x7E]', '', text)

def generate_pdf_voucher(tran_id, diamond, actual_wp, userid, zoneid, username, status, coin_value, my_bal, formatted_date):
    # Use a temporary directory to save the file
    temp_dir = gettempdir()
    file_path = os.path.join(temp_dir, f"Payment_Voucher_{tran_id}.pdf")

    # Initialize the PDF object
    pdf = FPDF(format='A4')
    pdf.add_page()

    # Add a logo
    logo_path = "lhp_logo.jpg"
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=8, w=30)
        pdf.ln(20)

    # Set title
    pdf.set_font("Helvetica", style="B", size=16)
    pdf.cell(0, 10, "Payment Voucher", ln=True, align="C")
    pdf.ln(10)

    # Voucher details
    pdf.set_font("Helvetica", size=12)
    fields = [
        ("Transaction ID", tran_id),
        ("Product", f"{diamond} Diamonds"),
        ("Successful WP", actual_wp),
        ("User ID", userid),
        ("Zone ID", zoneid),
        ("Username", username),
        ("Status", status),
        ("Debited from Balance", f"${coin_value:.2f}"),
        ("Remaining Balance", f"${my_bal:.2f}"),
        ("Date", formatted_date)
    ]

    # Add details to PDF, removing unsupported characters
    for field, value in fields:
        clean_field = remove_unsupported_characters(field)
        clean_value = remove_unsupported_characters(str(value))
        pdf.cell(50, 10, clean_field, border=1)
        pdf.cell(80, 10, clean_value, border=1)
        pdf.ln()

    # Save the PDF
    pdf.output(file_path)
    return file_path
async def process_toupup_voucher(message, tran_id, diamond, actual_wp, userid, zoneid, username, status, coin_value, my_bal, formatted_date):

    # Generate PDF voucher
    file_path = generate_pdf_voucher(
        tran_id=tran_id,
        diamond=diamond,
        actual_wp=actual_wp,
        userid=userid,
        zoneid=zoneid,
        username=username,
        status=status,
        coin_value=coin_value,
        my_bal=my_bal,
        formatted_date=formatted_date
    )



    # Send beautified voucher text
    await send_beautified_voucher(message, tran_id, diamond, actual_wp, userid, zoneid, username, status, coin_value, my_bal, formatted_date)

    pdf_file = FSInputFile(file_path)
    await message.answer_document(pdf_file, caption="🎟️ Here is your payment voucher as a PDF.")



@dp.message(F.text.regexp(r'.topup'))
async def toupup(message: types.Message,state: FSMContext)-> None:
    async def process_toupup(message_text: str):
        price_l = {
                '13': 61.50,
                '23': 122.00,
                '25': 177.50,
                '26': 480.00,
                '27': 1453.00,
                '28': 2424.00,
                '29': 3660.00,
                '30': 607.00,
        '20340':229.71,
        '33':402.5,
        '22590':39,
        '22591':116.9,
        '22592':187.5,
        '22593':385,
        '22594':39
            }
        id_list = ['13','23','25','23+23','25+23','25+25','25+25+13','26','26+23','26+23+23','26+26','27','28','29','30','','','','','','','','','','','25+13','26+25+13','26+13','27+26','26+25','13+23+23','26+25+23','20340','33','22590','22591','22592','22593','22594']
        user_id = message.from_user.id
        main_user = user_id
        my_bal = db.fetchone('SELECT amount FROM balance WHERE user_id=?', (user_id,))
        my_bal = float(''.join(map(str, my_bal)))
        mesg = re.sub(r"[\n\t\s]*", "", message.text)
        print(mesg)
        userid = mesg.split("(")[0].split(".topup")[1]
        zoneid = mesg.split("(")[1].split(")")[0]
        diamond = mesg.split(")")[1]
        if "wp" in diamond:
            diamond = diamond.strip()
            pack_number = diamond.split("wp")[0]
            actual_wp = 0
            pri = db.fetchall('SELECT package_no,diamond,price FROM dia_price')
            coin_value = next((y for z,x, y in pri if x == diamond), None)
            package_no = next((z for z,x, y in pri if x == diamond), None)
            get_condition = await smile_one.get_role(userid,zoneid,'16642')
            current_date = datetime.now()
            formatted_date = current_date.strftime("%d %B %Y")
            data = json.loads(get_condition)           
            if data["message"]=="success":
                username = data['username']
                tran_id = "\n"
                if float(coin_value) < float(my_bal):
                    for i in range(int(pack_number)):
                        purchase = await smile_one.get_purchase(userid,zoneid,'16642')
                        try:
                            pur_data = json.loads(purchase)
                            if pur_data['message'] != 'success':
                                status = "fail"
                                print("fail")
                                coin_value = coin_value - 76
                            else:
                                actual_wp = actual_wp + 1
                                status = "success"
                                print("success")
                                tran_id += "transcation_id:" + pur_data['order_id']+"\n"
                        except json.JSONDecodeError as e:
                            coin_value = coin_value - 76
                    print("first:",str(my_bal))
                    my_bal = my_bal - coin_value
                    print("now:",str(my_bal))
                    db.query("insert into transcation (user_id,diamond,price,t_date,status,main_user) values (?,?,?,?,?,?)",(user_id,diamond,coin_value,formatted_date,status,main_user))
                    db.query("update balance set amount=? where user_id=?",(my_bal,user_id))
                    await message.answer(f"successful topup")
                    try:
                        await process_toupup_voucher(
                                            message,
                                            tran_id=tran_id,
                                            diamond=diamond,
                                            actual_wp=actual_wp,
                                            userid=userid,
                                            zoneid=zoneid,
                                            username=username,
                                            status=status,
                                            coin_value=coin_value,
                                            my_bal=my_bal,
                                            formatted_date=formatted_date
                                        )

                    except:
                        print("Exception in")
                        await asyncio.sleep(10)
                        await process_toupup_voucher(
                                            message,
                                            tran_id=tran_id,
                                            diamond=diamond,
                                            actual_wp=actual_wp,
                                            userid=userid,
                                            zoneid=zoneid,
                                            username=username,
                                            status=status,
                                            coin_value=coin_value,
                                            my_bal=my_bal,
                                            formatted_date=formatted_date
                                        )
                        print("Exception done")
                else:
                    await message.answer(f"Insufficient Balance...")
            else:
                await message.answer(f" {userid} {zoneid} Not Valid Acoount")
        else:
            diamond = diamond
            pri = db.fetchall('SELECT package_no,diamond,price FROM dia_price WHERE package_no NOT BETWEEN 16 AND 25')
            coin_value = next((y for z,x, y in pri if str(x) == str(diamond)), None)
            package_no = next((z for z,x, y in pri if str(x) == str(diamond)), None)
            product_id = id_list[package_no-1]
            if "+" in product_id:
                product_id_list = product_id.split("+")
                get_condition = await smile_one.get_role(userid,zoneid,product_id_list[0])
                current_date = datetime.now()
                formatted_date = current_date.strftime("%d %B %Y")
                data = json.loads(get_condition)            
                if data["message"]=="success":
                    username = data['username']
                    tran_id = "\n"
                    if (coin_value) < my_bal:
                        for i in product_id_list:
                            purchase = await smile_one.get_purchase(userid,zoneid,i)
                            try:
                                pur_data = json.loads(purchase)
                                if pur_data["message"] != 'success':
                                    status = "fail"
                                    print(coin_value)
                                    print(price_l[str(i)])
                                    coin_value = coin_value - price_l[str(i)]
                                else:
                                    status = "success"
                                    tran_id += "transcation_id:" + pur_data['order_id']+"\n"
                            except json.JSONDecodeError as e:
                                coin_value = coin_value - price_l[str(i)]
                        print("fist:",str(my_bal))
                        my_bal = my_bal - coin_value
                        print("now:",str(my_bal))
                        db.query("insert into transcation (user_id,diamond,price,t_date,status,main_user) values (?,?,?,?,?,?)",(user_id,diamond,coin_value,formatted_date,status,main_user))
                        db.query("update balance set amount=? where user_id=?",(my_bal,user_id))
                        actual_wp = 0
                        try:
                            await process_toupup_voucher(
                                                message,
                                                tran_id=tran_id,
                                                diamond=diamond,
                                                actual_wp=actual_wp,
                                                userid=userid,
                                                zoneid=zoneid,
                                                username=username,
                                                status=status,
                                                coin_value=coin_value,
                                                my_bal=my_bal,
                                                formatted_date=formatted_date
                                            )
                        except:
                            print("Exception in")
                            await asyncio.sleep(10)
                            await process_toupup_voucher(
                                                message,
                                                tran_id=tran_id,
                                                diamond=diamond,
                                                actual_wp=actual_wp,
                                                userid=userid,
                                                zoneid=zoneid,
                                                username=username,
                                                status=status,
                                                coin_value=coin_value,
                                                my_bal=my_bal,
                                                formatted_date=formatted_date
                                            )
                            print("Exception Done")
                    else:
                        await message.answer(f"Insufficient Balance")
                else:
                    await message.answer(f"{userid} {zoneid} Not Valid Acoount")
            else:        
                get_condition = await smile_one.get_role(userid,zoneid,product_id)
                current_date = datetime.now()
                formatted_date = current_date.strftime("%d %B %Y")
                data = json.loads(get_condition)            
                if data["message"]=="success":
                    username = data['username']
                    tran_id = "\n"
                    if (coin_value) < my_bal:
                        print(product_id)
                        purchase = await smile_one.get_purchase(userid,zoneid,product_id)
                        pur_data = json.loads(purchase)
                        if pur_data["message"] != 'success':
                            status = "fail"
                            print(coin_value)
                            print(price_l[str(product_id)])
                            coin_value = coin_value - price_l[str(product_id)]
                        else:
                            status = "success"
                            tran_id += "transcation_id:" + pur_data['order_id'] +"\n"
                        print("fist:",str(my_bal))
                        my_bal = my_bal - coin_value
                        print("now:",str(my_bal))
                        db.query("insert into transcation (user_id,diamond,price,t_date,status,main_user) values (?,?,?,?,?,?)",(user_id,diamond,coin_value,formatted_date,status,main_user))
                        db.query("update balance set amount=? where user_id=?",(my_bal,user_id))
                        await message.answer(f"successful topup")
                        actual_wp = 0
                        try:
                            await process_toupup_voucher(
                                                message,
                                                tran_id=tran_id,
                                                diamond=diamond,
                                                actual_wp=actual_wp,
                                                userid=userid,
                                                zoneid=zoneid,
                                                username=username,
                                                status=status,
                                                coin_value=coin_value,
                                                my_bal=my_bal,
                                                formatted_date=formatted_date
                                            )
                        except:
                            print("Exception in")
                            await asyncio.sleep(10)

                            await process_toupup_voucher(
                                                message,
                                                tran_id=tran_id,
                                                diamond=diamond,
                                                actual_wp=actual_wp,
                                                userid=userid,
                                                zoneid=zoneid,
                                                username=username,
                                                status=status,
                                                coin_value=coin_value,
                                                my_bal=my_bal,
                                                formatted_date=formatted_date
                                            )
                            print("Exception done")
                    else:
                        await message.answer(f"Insufficient Balance...")
                else:
                    await message.answer(f"{userid} {zoneid} is not Valid Acoount")
    await asyncio.gather(process_toupup(message.text))

@dp.message(F.text.regexp(r'.ph_topup'))
async def toupup_ph(message: types.Message,state: FSMContext)-> None:
    async def process_toupup_ph(message_text: str):
        price_l = {
                '212': 9.50,
                '213': 20.00,
                '214': 47.50,
                '215': 95.00,
                '216': 190.00,
                '217': 285.00,
                '218': 475.00,
                '219': 950.00,
		'20338':229.71
            }
        id_list = ['212','213','214','215','216','217','218','219','20338']
        user_id = message.from_user.id
        main_user = user_id
        my_bal = db.fetchone('SELECT amount FROM balance_ph WHERE user_id=?', (user_id,))
        my_bal = float(''.join(map(str, my_bal)))
        mesg = re.sub(r"[\n\t\s]*", "", message.text)
        print(mesg)
        userid = mesg.split("(")[0].split(".ph_topup")[1]
        zoneid = mesg.split("(")[1].split(")")[0]
        diamond = mesg.split(")")[1]
        diamond = int(diamond)
        pri = db.fetchall('SELECT package_no,diamond,price FROM dia_price_ph')
        coin_value = next((y for z,x, y in pri if int(x) == diamond), None)
        package_no = next((z for z,x, y in pri if int(x) == diamond), None)
        product_id = id_list[package_no-1]
        get_condition = smile_one_ph.get_role(userid,zoneid,product_id)
        current_date = datetime.now()
        formatted_date = current_date.strftime("%d %B %Y")
        data = json.loads(get_condition)            
        if data["message"]=="success":
            username = data['username']
            tran_id = "\n"
            if (coin_value) < my_bal:
                print(product_id)
                purchase = smile_one_ph.get_purchase(userid,zoneid,product_id)
                try:
                    pur_data = json.loads(purchase)
                    if pur_data["message"] != 'success':
                        status = "fail"
                        print(coin_value)
                        print(price_l[str(product_id)])
                        coin_value = coin_value - price_l[str(product_id)]
                    else:
                        status = "success"
                        tran_id += "transcation_id:" + pur_data['order_id'] +"\n"
                except json.JSONDecodeError as e:
                    coin_value = coin_value - price_l[str(product_id)]
                print("fist:",str(my_bal))
                my_bal = my_bal - coin_value
                print("now:",str(my_bal))
                db.query("insert into transcation (user_id,diamond,price,t_date,status,main_user) values (?,?,?,?,?,?)",(user_id,diamond,coin_value,formatted_date,status,main_user))
                db.query("update balance_ph set amount=? where user_id=?",(my_bal,user_id))
                await message.answer(f"successful topup")
                actual_wp = 0
                try:
                    await process_toupup_voucher(
                                                message,
                                                tran_id=tran_id,
                                                diamond=diamond,
                                                actual_wp=actual_wp,
                                                userid=userid,
                                                zoneid=zoneid,
                                                username=username,
                                                status=status,
                                                coin_value=coin_value,
                                                my_bal=my_bal,
                                                formatted_date=formatted_date
                                            )
                except:
                    print("Exception in")
                    await asyncio.sleep(10)
                    await process_toupup_voucher(
                                                message,
                                                tran_id=tran_id,
                                                diamond=diamond,
                                                actual_wp=actual_wp,
                                                userid=userid,
                                                zoneid=zoneid,
                                                username=username,
                                                status=status,
                                                coin_value=coin_value,
                                                my_bal=my_bal,
                                                formatted_date=formatted_date
                                            )

                    print("Exception done")
            else:
                await message.answer(f"Insufficient Balance...")
        else:
            await message.answer(f"{userid} {zoneid} is not Valid Acoount")
    await asyncio.gather(process_toupup_ph(message.text))

@dp.message(F.text.regexp(r'.bulktopup'))
async def bulktopup(message: types.Message,state: FSMContext)-> None:
    async def process_bulk_toupup(message_text: str):
        price_l = {
                '13': 61.50,
                '23': 122.00,
                '25': 177.50,
                '26': 480.00,
                '27': 1453.00,
                '28': 2424.00,
                '29': 3660.00,
                '30': 607.00,
        '20340':229.71,
        '33':402.5,
        '22590':39,
        '22591':116.9,
        '22592':187.5,
        '22593':385,
        '22594':39
            }
        id_list = ['13','23','25','23+23','25+23','25+25','25+25+13','26','26+23','26+23+23','26+26','27','28','29','30','','','','','','','','','','','25+13','26+25+13','26+13','27+26','26+25','13+23+23','26+25+23','20340','33','22590','22591','22592','22593','22594']
        user_id = message.from_user.id
        main_user = user_id
        voucher = f"\tVoucher\n\t============\n\n"
        my_bal = db.fetchone('SELECT amount FROM balance WHERE user_id=?', (user_id,))
        my_bal = float(''.join(map(str, my_bal)))
        block = message.text.split(",")
        block = list(filter(None, block))
        current_date = datetime.now()
        formatted_date = current_date.strftime("%d %B %Y")
        for i in range(len(block)):
            mesg = re.sub(r"[\n\t\s]*", "", block[i])
            print(mesg)
            three_value = re.findall(r'\d+\(\d+\)(\d+wp|\d+)',mesg)
            two_value = re.findall(r'\d+\(\d+\)',mesg)
            diamond  = three_value[0]
            userid = two_value[0].split("(")[0]
            zoneid = two_value[0].split("(")[1].split(")")[0]
            if "wp" in diamond:
                pack_number = diamond.split("wp")[0]
                actual_wp = 0
                pri = db.fetchall('SELECT package_no,diamond,price FROM dia_price')
                coin_value = next((y for z,x, y in pri if x == diamond), None)
                package_no = next((z for z,x, y in pri if x == diamond), None)
                get_condition = await smile_one.get_role(userid,zoneid,'16642')
                current_date = datetime.now()
                formatted_date = current_date.strftime("%d %B %Y")
                data = json.loads(get_condition)  
                if data["message"]=="success":
                    username = data['username']
                    tran_id = "\n"
                    if (coin_value) < my_bal:
                        for i in range(int(pack_number)):
                            purchase = await smile_one.get_purchase(userid,zoneid,'16642')
                            try:
                                pur_data = json.loads(purchase)
                                if pur_data["message"] != 'success':
                                    status = "fail"
                                    print(coin_value)
                                    print("76")
                                    print("fail")
                                    coin_value = coin_value - 76
                                else:
                                    actual_wp = actual_wp + 1
                                    status = "success"
                                    print(status)
                                    tran_id += "transcation_id:" + pur_data['order_id'] + "\n"
                            except json.JSONDecodeError as e:
                                coin_value = coin_value - 76
                        print("bulk first:",str(my_bal))
                        my_bal = my_bal - coin_value
                        print("bulk now:",str(my_bal))
                        db.query("insert into transcation (user_id,diamond,price,t_date,status,main_user) values (?,?,?,?,?,?)",(user_id,diamond,coin_value,formatted_date,status,main_user))
                        db.query("update balance set amount=? where user_id=?",(my_bal,user_id))
                        await message.answer(f"successful topup")
                        voucher += f"\n\n\ntransaction id:\t{tran_id}product:\t💎{hbold(diamond)}\nsuccessful_wp:\t{hbold(actual_wp)}\nuserid:\t👤{hbold(userid)}\t🆔{hbold(zoneid)}\nusername:{hbold(username)}\nStatus: {hbold(status)}\n\n\nDebited From Balance:\t{hbold(coin_value)}\nBalance:\t${hbold(my_bal)}"
                    else:
                        await message.answer(f"Insufficient Balance")
                else:
                    await message.answer(f"{userid} {zoneid} is not Valid Acoount")
            else:
                diamond = diamond
                pri = db.fetchall('SELECT package_no,diamond,price FROM dia_price WHERE package_no NOT BETWEEN 16 AND 25')
                coin_value = next((y for z,x, y in pri if str(x) == str(diamond)), None)
                package_no = next((z for z,x, y in pri if str(x) == str(diamond)), None)
                product_id = id_list[package_no-1]
                if "+" in product_id:
                    product_id_list = product_id.split("+")
                    get_condition = await smile_one.get_role(userid,zoneid,product_id_list[0])
                    current_date = datetime.now()
                    formatted_date = current_date.strftime("%d %B %Y")
                    data = json.loads(get_condition)            
                    if data["message"]=="success":
                        username = data['username']
                        tran_id = "\n"
                        if (coin_value) < my_bal:
                            for i in product_id_list:
                                purchase = await smile_one.get_purchase(userid,zoneid,i)
                                try:
                                    pur_data = json.loads(purchase)
                                    if pur_data["message"] != 'success':
                                        status = "fail"
                                        print(coin_value)
                                        print(price_l[str(i)])
                                        coin_value = coin_value - price_l[str(i)]
                                    else:
                                        status = "success"
                                        tran_id += "transcation_id:" + pur_data['order_id']+ "\n"
                                except json.JSONDecodeError as e:
                                    coin_value = coin_value - price_l[str(i)]
                            print("bulk first:",str(my_bal))
                            my_bal = my_bal - coin_value
                            print("bulk now:",str(my_bal))
                            db.query("insert into transcation (user_id,diamond,price,t_date,status,main_user) values (?,?,?,?,?,?)",(user_id,diamond,coin_value,formatted_date,status,main_user))
                            db.query("update balance set amount=? where user_id=?",(my_bal,user_id))
                            await message.answer(f"successful topup")
                            voucher += f"\n\n\ntransaction id:\t{tran_id}product:\t💎{hbold(diamond)}\nuserid:\t👤{hbold(userid)}\t🆔{hbold(zoneid)}\nusername:{hbold(username)}\nStatus: {hbold(status)}\n\n\nDebited From Balance:\t{hbold(coin_value)}\nBalance:\t${hbold(my_bal)}"
                        else:
                            await message.answer(f"Insufficient Balance")
                    else:
                        await message.answer(f"{userid} {zoneid} is not Valid Acoount")
                else:
                    get_condition = await smile_one.get_role(userid,zoneid,product_id)
                    current_date = datetime.now()
                    formatted_date = current_date.strftime("%d %B %Y")
                    data = json.loads(get_condition)            
                    if data["message"]=="success":
                        username = data['username']
                        tran_id = "\n"
                        if (coin_value) < my_bal:
                            purchase = await smile_one.get_purchase(userid,zoneid,product_id)
                            pur_data = json.loads(purchase)
                            if pur_data["message"] != 'success':
                                status = "fail"
                                print(coin_value)
                                print(price_l[str(product_id)])
                                coin_value = coin_value - price_l[str(product_id)]
                            else:
                                status = "success"
                                tran_id += "transcation_id:" + pur_data['order_id']+ "\n"
                            print("bulk first:",str(my_bal))
                            my_bal = my_bal - coin_value
                            print("bulk now:",str(my_bal))
                            db.query("insert into transcation (user_id,diamond,price,t_date,status,main_user) values (?,?,?,?,?,?)",(user_id,diamond,coin_value,formatted_date,status,main_user))
                            db.query("update balance set amount=? where user_id=?",(my_bal,user_id))
                            await message.answer(f"successful topup")
                            voucher += f"\n\n\n{tran_id}product:\t💎{hbold(diamond)}\nuserid:\t👤{hbold(userid)}\t🆔{hbold(zoneid)}\nusername:{hbold(username)}\nStatus: {hbold(status)}\n\n\nDebited From Balance:\t{hbold(coin_value)}\nBalance:\t${hbold(my_bal)}"
                        else:
                            await message.answer(f"{userid} {zoneid} Insufficient Balance...")
                    else:
                        await message.answer(f"{userid} {zoneid} is not Valid Acoount")
        voucher += f"\n{formatted_date}"
        try:
            await message.answer(voucher)
        except:
            print("exception in")
            await asyncio.sleep(10)
            await message.answer(voucher)
            print("exception done")
    await asyncio.gather(process_bulk_toupup(message.text))

@dp.message(F.text.regexp(r'.ph_bulktopup'))
async def bulktopup_ph(message: types.Message,state: FSMContext)-> None:
    async def process_bulk_toupup_ph(message_text: str):
        price_l = {
                '212': 9.50,
                '213': 20.00,
                '214': 47.50,
                '215': 95.00,
                '216': 190.00,
                '217': 285.00,
                '218': 475.00,
                '219': 950.00,
		'20338':229.71
            }
        id_list = ['212','213','214','215','216','217','218','219','20338']
        user_id = message.from_user.id
        main_user = user_id
        voucher = f"\tVoucher\n\t============\n\n"
        my_bal = db.fetchone('SELECT amount FROM balance_ph WHERE user_id=?', (user_id,))
        print(my_bal)
        my_bal = float(''.join(map(str, my_bal)))
        block = message.text.split(",")
        block = list(filter(None, block))
        current_date = datetime.now()
        formatted_date = current_date.strftime("%d %B %Y")
        for i in range(len(block)):
            mesg = re.sub(r"[\n\t\s]*", "", block[i])
            print(mesg)
            three_value = re.findall(r'\d+\(\d+\)(\d+wp|\d+)',mesg)
            two_value = re.findall(r'\d+\(\d+\)',mesg)
            diamond  = three_value[0]
            userid = two_value[0].split("(")[0]
            zoneid = two_value[0].split("(")[1].split(")")[0]
            diamond = int(diamond)
            pri = db.fetchall('SELECT package_no,diamond,price FROM dia_price_ph')
            coin_value = next((y for z,x, y in pri if int(x) == diamond), None)
            package_no = next((z for z,x, y in pri if int(x) == diamond), None)
            product_id = id_list[package_no-1]
            get_condition = smile_one_ph.get_role(userid,zoneid,product_id)
            current_date = datetime.now()
            formatted_date = current_date.strftime("%d %B %Y")
            data = json.loads(get_condition)            
            if data["message"]=="success":
                username = data['username']
                tran_id = "\n"
                if (coin_value) < my_bal:
                    purchase = smile_one_ph.get_purchase(userid,zoneid,product_id)
                    pur_data = json.loads(purchase)
                    if pur_data["message"] != 'success':
                        status = "fail"
                        print(coin_value)
                        print(price_l[str(product_id)])
                        coin_value = coin_value - price_l[str(product_id)]
                    else:
                        status = "success"
                        tran_id += "transcation_id:" + pur_data['order_id']+ "\n"
                    print("bulk first:",str(my_bal))
                    my_bal = my_bal - coin_value
                    print("bulk now:",str(my_bal))
                    db.query("insert into transcation (user_id,diamond,price,t_date,status,main_user) values (?,?,?,?,?,?)",(user_id,diamond,coin_value,formatted_date,status,main_user))
                    db.query("update balance_ph set amount=? where user_id=?",(my_bal,user_id))
                    await message.answer(f"successful topup")
                    voucher += f"\n\n\n{tran_id}product:\t💎{hbold(diamond)}\nuserid:\t👤{hbold(userid)}\t🆔{hbold(zoneid)}\nusername:{hbold(username)}\nStatus: {hbold(status)}\n\n\nDebited From Balance:\t{hbold(coin_value)}\nBalance:\t${hbold(my_bal)}"
                else:
                    await message.answer(f"{userid} {zoneid} Insufficient Balance...")
            else:
                await message.answer(f"{userid} {zoneid} is not Valid Acoount")
        voucher += f"\n{formatted_date}"
        try:
            await message.answer(voucher)
        except:
            print("exception in")
            await asyncio.sleep(10)
            await message.answer(voucher)
            print("exception done")
    await asyncio.gather(process_bulk_toupup_ph(message.text))

@dp.message( F.text.regexp(r'\.check_balance'))
async def check_balance(message: types.Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    # Fetching balance from the database
    my_bal = db.fetchone('SELECT amount FROM balance WHERE user_id=?', (user_id,))
    my_bal_ph = db.fetchone('SELECT amount FROM balance_ph WHERE user_id=?', (user_id,))
    
    # Preparing responses
    balance_message = f"Your balance is: {hbold(my_bal[0])} Coins 😊"
    balance_ph_message = f"Your PH balance is: {hbold(my_bal_ph[0])} Coins 😊"
    
    # Sending responses
    await message.answer(balance_message)
    await message.answer(balance_ph_message)

    
# States for selecting date range
class DateRangeState(StatesGroup):
    awaiting_start_date = State()
    awaiting_end_date = State()


class DateSingleState(StatesGroup):
    awaiting_single_date = State()

# Helper function to fetch data
def fetch_transactions(user_id, start_date=None, end_date=None):
    query = "SELECT diamond FROM transcation WHERE user_id=?"
    params = [user_id]

    if start_date and end_date:
        query += " AND t_date BETWEEN ? AND ?"
        params.extend([start_date, end_date])
    elif start_date:
        query += " AND t_date=?"
        params.append(start_date)

    return db.fetchall(query, params)

def generate_voucher_pdf(transactions, title, filename):
    pdf = FPDF()
    pdf.add_page()
    
    # Add logo
    logo_path = "lhp_logo.jpg"
    if logo_path:
        pdf.image(logo_path, x=10, y=8, w=30)  # Adjust the x, y, and w as needed
        pdf.ln(20)  # Add some space after the logo
    
    # Title
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(200, 10, txt=title, ln=True, align="C")
    pdf.ln(10)

    # Add table header
    pdf.set_font("Arial", style="B", size=12)
    pdf.set_fill_color(200, 220, 255)  # Light blue background for the header
    pdf.cell(50, 10, "Diamond", border=1, align="C", fill=True)
    pdf.cell(50, 10, "Count", border=1, align="C", fill=True)
    pdf.ln()

    # Counting diamonds
    number_count = {}
    for trans in transactions:
        diamond = trans[0]
        number_count[diamond] = number_count.get(diamond, 0) + 1

    # Table rows
    pdf.set_font("Arial", size=10)
    for diamond, count in number_count.items():
        pdf.cell(50, 10, txt=str(diamond), border=1, align="C")
        pdf.cell(50, 10, txt=str(count), border=1, align="C")
        pdf.ln()

    # Footer
    pdf.set_y(-15)
    pdf.set_font("Arial", size=8)
    pdf.cell(0, 10, "Generated by LHP Game Store © 2025", align="C")

    # Save to file
    pdf.output(filename)

# Command to start voucher options 
@dp.message(F.text == "/voucher")
async def voucher_options(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Today", callback_data="today")],
        [InlineKeyboardButton(text="Yesterday", callback_data="yesterday")],
        [InlineKeyboardButton(text="This Month", callback_data="this_month")],
        [InlineKeyboardButton(text="All Time", callback_data="all_time")],
        [InlineKeyboardButton(text="Select Date", callback_data="select_date")],
        [InlineKeyboardButton(text="Select Range", callback_data="select_range")],
    ])
    await message.answer("Choose an option to view your vouchers:", reply_markup=keyboard)

# Callback handler for "Today"
@dp.callback_query(F.data == "today")
async def process_today(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    today = datetime.now().strftime("%Y-%m-%d")
    transactions = fetch_transactions(user_id, start_date=today)

    filename = f"voucher_today_{user_id}.pdf"
    generate_voucher_pdf(transactions, f"Voucher for {today}", filename)

    # Use FSInputFile to send the file
    file_input = FSInputFile(filename)
    await callback_query.message.answer_document(file_input)

# Callback handler for "Yesterday"
@dp.callback_query(F.data == "yesterday")
async def process_yesterday(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    transactions = fetch_transactions(user_id, start_date=yesterday)

    filename = f"voucher_yesterday_{user_id}.pdf"
    generate_voucher_pdf(transactions, f"Voucher for {yesterday}", filename)
    file_input = FSInputFile(filename)
    await callback_query.message.answer_document(file_input)

# Callback handler for "This Month"
@dp.callback_query(F.data == "this_month")
async def process_this_month(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    today = datetime.now()
    start_date = today.replace(day=1).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")
    transactions = fetch_transactions(user_id, start_date=start_date, end_date=end_date)

    filename = f"voucher_this_month_{user_id}.pdf"
    generate_voucher_pdf(transactions, f"Voucher for {start_date} to {end_date}", filename)
    file_input = FSInputFile(filename)
    await callback_query.message.answer_document(file_input)

# Callback handler for "All Time"
@dp.callback_query(F.data == "all_time")
async def process_all_time(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    transactions = fetch_transactions(user_id)

    filename = f"voucher_all_time_{user_id}.pdf"
    generate_voucher_pdf(transactions, "Voucher for All Time", filename)
    file_input = FSInputFile(filename)
    await callback_query.message.answer_document(file_input)

# Callback handler for "Select Date"
@dp.callback_query(F.data == "select_date")
async def process_select_date(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Please type the date in the format `YYYY-MM-DD`:")
    await state.set_state(DateSingleState.awaiting_single_date)

@dp.message(DateSingleState.awaiting_single_date, F.text.regexp(r"^\d{4}-\d{2}-\d{2}$"))
async def handle_single_date(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    selected_date = message.text
    transactions = fetch_transactions(user_id, start_date=selected_date)

    filename = f"voucher_{selected_date}_{user_id}.pdf"
    generate_voucher_pdf(transactions, f"Voucher for {selected_date}", filename)
    file_input = FSInputFile(filename)
    await message.answer_document(file_input)
    await state.clear()

# Callback handler for "Select Range"
@dp.callback_query(F.data == "select_range")
async def process_select_range(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Please type the start date in the format `YYYY-MM-DD`:")
    await state.set_state(DateRangeState.awaiting_start_date)

@dp.message(DateRangeState.awaiting_start_date, F.text.regexp(r"^\d{4}-\d{2}-\d{2}$"))
async def handle_start_date(message: types.Message, state: FSMContext):
    await state.update_data(start_date=message.text)
    await message.answer("Please type the end date in the format `YYYY-MM-DD`:")
    await state.set_state(DateRangeState.awaiting_end_date)

@dp.message(DateRangeState.awaiting_end_date, F.text.regexp(r"^\d{4}-\d{2}-\d{2}$"))
async def handle_end_date(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    start_date = data["start_date"]
    end_date = message.text

    transactions = fetch_transactions(user_id, start_date=start_date, end_date=end_date)

    filename = f"voucher_{start_date}_to_{end_date}_{user_id}.pdf"
    generate_voucher_pdf(transactions, f"Voucher for {start_date} to {end_date}", filename)
    file_input = FSInputFile(filename)
    await message.answer_document(file_input)
    await state.clear()


@dp.message( F.text.regexp(r'/menu'))
async def show_menu(message: types.Message) -> None:
    # Inline keyboard for navigation
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 View Price List", callback_data="price_list")],
        [InlineKeyboardButton(text="💎 Top-up Instructions", callback_data="topup_instructions")],
        [InlineKeyboardButton(text="⚖️ Check Balance", callback_data="check_balance")],
        [InlineKeyboardButton(text="📖 View Top-up History", callback_data="view_history")]
    ])
    
    # Beautified menu message
    await message.answer(
        "<b>🏷️ Commands Menu:</b>\n\n"
        "🪙 <code>.price_list</code> — <i>View the price list</i>.\n"
        "💎 <code>.topup userid(zoneid) diamonds</code> — <i>Top up for a single account</i>.\n"
        "💎 <code>.topup_ph userid(zoneid) diamonds</code> — <i>Top up for a single account (PH)</i>.\n"
        "💎 <code>.bulktopup userid(zoneid) diamonds,userid(zoneid) diamonds,...</code> — <i>Bulk top-up for multiple accounts</i>.\n"
        "💎 <code>.ph_bulktopup userid(zoneid) diamonds,userid(zoneid) diamonds,...</code> — <i>Bulk top-up for multiple accounts (PH)</i>.\n"
        "⚖️ <code>.check_balance</code> — <i>Check your balance</i>.\n"
        "📜 <code>.history</code> — <i>Check your top-up history</i>.\n\n"
        "<b>🎯 Quick Actions:</b>\n"
        "<i>Use the buttons below for faster navigation!</i>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "view_history")
async def history_callback(callback_query: types.CallbackQuery) -> None:
    await callback_query.message.answer(f"💎 Use `{hcode('.history')}` to check your top-up history")
    await callback_query.answer()

@dp.callback_query(F.data == "price_list")
async def price_list_callback(callback_query: types.CallbackQuery) -> None:
    await callback_query.message.answer(f"💎 Use `{hcode('.price_list')}` to view the price list!")
    await callback_query.answer()

@dp.callback_query(F.data == "topup_instructions")
async def topup_instructions_callback(callback_query: types.CallbackQuery) -> None:
    await callback_query.message.answer(
        "💎 Top-up Instructions:\n\n"
        f"👉 {hcode('.topup userid(zoneid) diamonds')} -> Top up for a single account.\n"
        f"👉 {hcode('.bulktopup userid(zoneid) diamonds,userid(zoneid) diamonds,...')} -> Bulk top up for multiple accounts.\n"
        "💡 Replace `userid`, `zoneid`, and `diamonds` with appropriate values."
    )
    await callback_query.answer()

@dp.callback_query(F.data == "check_balance")
async def check_balance_callback(callback_query: types.CallbackQuery) -> None:
    await callback_query.message.answer(f"⚖️ Use `{hcode('.check_balance')}` to view your account balance.")
    await callback_query.answer()





async def main() -> None:

    await bot.set_my_commands([
        BotCommand(command="/start",description="to see login"),
        BotCommand(command="/voucher",description="to see total transcations"),
        BotCommand(command="/menu",description="to see menu"),
        ]
        )
    await dp.start_polling(bot)




if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

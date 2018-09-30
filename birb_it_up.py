import requests
import re
import os
import csv
import math
import threading
import smtplib
from email.mime.text import MIMEText 
from email.mime.multipart import MIMEMultipart 
from email.mime.base import MIMEBase 
from email import encoders

def send_email(
    username = '',
    password = '',
    msg_from = '',
    msg_to = '',
    msg_cc = '',
    msg_bcc = '',
    msg_subject = '',
    msg_body = '',
    msg_attach = []):
    
    msg = MIMEMultipart()    
    msg['From'] = msg_from
    msg['To'] = msg_to
    msg['Cc'] = msg_cc
    msg['Subject'] = msg_subject 
    body = msg_body
    msg.attach(MIMEText(body, 'plain'))

    msg_all = []
    msg_all.extend(email_string_to_list(msg_to))
    msg_all.extend(email_string_to_list(msg_cc))
    msg_all.extend(email_string_to_list(msg_bcc))
    
    for i in range(len(msg_attach)):
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(msg_attach[i], 'rb').read())
        encoders.encode_base64(part)
        file_name = drop_path(str(msg_attach[i]))
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % file_name)
        msg.attach(part)

    text = msg.as_string() 
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo()
    server.starttls()
    server.login(username, password)
    server.sendmail(msg_from, msg_all, text)
    server.quit()

def drop_path(explicit_path):
    file_name = explicit_path.split('\\')
    file_name = file_name[len(file_name)-1]
    return file_name

def email_string_to_list(email_string):
    email_string = str(email_string).split(',')
    email_list = []
    for i in range(len(email_string)):
        email_list.append(email_string[i])
    return email_list

def re_month(text):
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
              'August', 'September', 'October', 'November', 'December']
    for i in range(len(months)):
        text = str(text).replace(str(months[i]), str(i+1).zfill(2))
    return text

def re_time_stamp(old_time):

    day = old_time[:2]
    month = old_time[2:4]
    year = old_time[4:8]
    hour = old_time[9:11]
    minute = old_time[12:14]
    second = old_time[15:18]
    new_time = str(year) + str(month) + str(day) + str(hour) + str(minute) + str(second)
    return new_time

def get_posts(url_page_text):
    post_pattern = r'<divclass="poster">.+?<hrclass="post_separator"/>'
    posts = re.findall(post_pattern, url_page_text, re.DOTALL)
    return posts

def get_time_stamp(post_text):
    time_stamp_pattern = r'\d{8}\,\d\d\:\d\d:\d\d'
    time_stamp = re.findall(time_stamp_pattern, post_text, re.DOTALL)
    return time_stamp[0]

def get_last_edit(post_text):
    time_stamp_pattern = r'LastEdit:.+(\d{8}\,\d\d\:\d\d:\d\d)'
    time_stamp = re.findall(time_stamp_pattern, post_text, re.DOTALL)
    if len(time_stamp) == 0:
        return '00000000000000'
    return time_stamp[0]

def get_poster(post_text):
    poster_patter = r'\"Viewtheprofileof(.+?)\"'
    poster = re.findall(poster_patter, post_text, re.DOTALL)
    if len(poster) == 0:
        return 'guest'
    return poster[0]

def birb_check(post_text):
    if 'https://i.imgur.com/vCthTwM.jpg' in post_text:
        return str(True)
    if 'http://i.imgur.com/mEDsgKy.jpg' in post_text:
        return str(True)
    return str(False)

def get_url_text(url):
    r = requests.get(url)
    text = r.text
    text = str(text).replace(' ','')
    text = re_month(text)
    return text

def sort_page(page_text, page_number):
    posts = get_posts(page_text)
    posters = list(map(get_poster, posts))
    time_stamps = list(map(get_time_stamp, posts))

    page_post_array = []
    for i in range(len(posts)):
        poster = get_poster(posts[i])
        time_stamp = re_time_stamp(get_time_stamp(posts[i]))
        birb = birb_check(posts[i])
        page_post_array.append([page_number, poster, time_stamp, birb])
    return page_post_array

def open_birb_log(birb_log = 'birb_log.csv'):
    if not os.path.exists(birb_log):
        open(birb_log, 'w')     
    birb_array = []
    with open(birb_log, newline='') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            birb_array.append(row)
    return birb_array

def row_check(birb_array, forum_array):
    unique_array = []
    for i in range(len(forum_array)):
        if not forum_array[i] in birb_array:
            unique_array.append(forum_array[i])
    return unique_array

def write_birb_log(birb_log = 'birb_log.csv', birb_array = []):
    with open(birb_log, 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',')
        for i in range(len(birb_array)):
            csv_writer.writerow(birb_array[i])

def new_birb_check(new_posts):
    for i in range(len(new_posts)):
        if new_posts[i][1] == 'eat_the_food' and new_posts[i][3] == 'True':
            return True
    return False

def edit_check(new_edit):
    if os.path.exists('top_post.txt'):
        text = open('top_post.txt', 'r')
        old_edit = text.read()
        text.close()
        if int(new_edit) > int(old_edit):
            text = open('top_post.txt', 'w')
            text.write(str(new_edit))
            text.close()
            return True
        
    if not os.path.exists('top_post.txt'):
        text = open('top_post.txt', 'w')
        text.write(str(new_edit))
        text.close()
        
def get_images(post_text):
    image_pattern = r'https://i\.imgur\.com.+?\.jpg'
    images = re.findall(image_pattern, post_text, re.DOTALL)
    images = list(set(images))
    return images

def list_to_string(image_list):
    image_string = ''
    for i in range(len(image_list)):
        image_string = str(image_string) + image_list[i] + '\n'
    return image_string

#--------------------------------------------------------------------------------------------------#
        
def check_sales_thread_edit(home_page = 'https://geekhack.org/index.php?topic=79513.0'):
    threading.Timer(300.0, check_sales_thread_edit).start()
    home_page_text = get_url_text(home_page)
    sales_post = get_posts(home_page_text)[0]
    last_edit = re_time_stamp(get_last_edit(sales_post))
    if edit_check(last_edit) == True:
        print('sales thread update!')
        image_list = get_images(sales_post)
        image_string = list_to_string(image_list)
        send_email(username = '',
                   password = '',
                   msg_to = '',
                   msg_bcc = '',
                   msg_subject = 'etf thread update!',
                   msg_body = 'https://geekhack.org/index.php?topic=79513.0\n' + str(image_string))

def birb_it_up():
    threading.Timer(60.0, birb_it_up).start()
    birb_array = open_birb_log()
    post_count = 50
    page_number = math.ceil((len(birb_array)+1) / 50)
    page_increment = ((math.ceil((len(birb_array)+1) / 50)) - 1) * 50

    while post_count == 50:
        url = 'https://geekhack.org/index.php?topic=79513.' + str(page_increment)
        text = get_url_text(url)
        page_post_array = sort_page(text, str(page_number))
        new_posts = row_check(birb_array, page_post_array)
        birb_array.extend(new_posts)
        write_birb_log(birb_array = birb_array)
        if new_birb_check(new_posts) == True:
            print('birb!')
            send_email(username = '',
                       password = '',
                       msg_to = '',
                       msg_bcc = '',
                       msg_subject = 'birb',
                       msg_body = str(url) + '\nhttps://geekhack.org/index.php?topic=79513.0')
    
        if len(new_posts) > 0:
            print('new posts added: ' + str(len(new_posts)))
            for i in range(len(new_posts)):
                print(birb_array[len(birb_array) - (len(new_posts)-i)])
        
        page_number += 1
        page_increment += 50
        post_count = len(page_post_array)

#--------------------------------------------------------------------------------------------------#
        
birb_it_up()
check_sales_thread_edit()

import serial
import time
import os
from PIL import Image, ImageDraw, ImageFont, ImageOps
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
from PIL import ImageTk

# === Settings ===
COM_PORT = 'COM3'
BAUDRATE = 115200
PRINTER_WIDTH = 384

# === Printing Functions ===
def print_text(text, font_size, align):
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    lines = text.split('\n')
    line_height = font.getbbox("Ag")[3] + 4
    img_height = line_height * len(lines) + 20

    image = Image.new('L', (PRINTER_WIDTH, img_height), color=255) 
    draw = ImageDraw.Draw(image)

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0] 

        if align == "center":
            text_x = (PRINTER_WIDTH - text_width) // 2
        elif align == "left":
            text_x = 0
        elif align == "right":
            text_x = PRINTER_WIDTH - text_width
        else: 
            text_x = (PRINTER_WIDTH - text_width) // 2

        text_y = i * line_height + 10 
        draw.text((text_x, text_y), line, font=font, fill=0)

    bw_image = image.point(lambda x: 0 if x < 128 else 255, '1')
    bitmap_data = convert_to_raster(bw_image)
    send_to_printer(bitmap_data)

def print_image(img_path):
    image = Image.open(img_path).convert('L')
    image = ImageOps.autocontrast(image)
    
    aspect_ratio = image.height / image.width
    new_height = int(PRINTER_WIDTH * aspect_ratio)
    image = image.resize((PRINTER_WIDTH, new_height), Image.LANCZOS) 
    
    dithered = image.convert('1')
    bitmap_data = convert_to_raster(dithered)
    send_to_printer(bitmap_data)

def convert_to_raster(img):
    img = img.convert('1') 
    width = img.width
    height = img.height
    width_bytes = (width + 7) // 8 
    
    data = bytearray()
    data += b'\x1D\x76\x30\x00' 
    data += (width_bytes % 256).to_bytes(1, 'little')
    data += (width_bytes // 256).to_bytes(1, 'little') 
    data += (height % 256).to_bytes(1, 'little') 
    data += (height // 256).to_bytes(1, 'little') 
    
    for y in range(height):
        for x_byte in range(width_bytes):
            byte = 0
            for bit in range(8):
                x = x_byte * 8 + bit
                if x < width: 
                    if img.getpixel((x, y)) == 0: 
                        byte |= 1 << (7 - bit)
            data.append(byte)
    return data

def send_to_printer(data):
    try:
        printer = serial.Serial(COM_PORT, baudrate=BAUDRATE, timeout=1)
        time.sleep(2) 
        
        printer.write(b'\x1B\x40') 
        printer.write(data)     
        printer.write(b'\n\n\n') 
        printer.close()     
        
        messagebox.showinfo("Print", "✅ Print completed successfully!")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# === GUI ===
root = tk.Tk()
root.title("Thermal Printer") 
root.geometry("500x600")

frame = ttk.Frame(root, padding=10)
frame.pack(fill=tk.BOTH, expand=True)

text_label = ttk.Label(frame, text="Enter text to print:")
text_label.pack()

text_entry = tk.Text(frame, height=3)
text_entry.pack(fill=tk.X)

font_size_label = ttk.Label(frame, text="Font Size:")
font_size_label.pack()
font_size_spinbox = tk.Spinbox(frame, from_=8, to=72)
font_size_spinbox.pack()

align_label = ttk.Label(frame, text="Alignment:")
align_label.pack()
align_var = tk.StringVar(value="center")
align_menu = ttk.Combobox(frame, textvariable=align_var, values=["left", "center", "right"])
align_menu.pack()

print_text_button = ttk.Button(
    frame,
    text="🖨️ Print Text", 
    command=lambda: print_text(
        text_entry.get("1.0", tk.END).strip(),
        int(font_size_spinbox.get()),
        align_var.get()
    )
)
print_text_button.pack(pady=10)

img_path_var = tk.StringVar()

def choose_image():
    file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
    if file_path:
        img_path_var.set(file_path) 
        preview_image(file_path) 

def preview_image(path):
    img = Image.open(path).convert('L')
    img.thumbnail((200, 200)) 
    tk_img = ImageTk.PhotoImage(img) 
    preview_label.config(image=tk_img) 
    preview_label.image = tk_img

choose_img_button = ttk.Button(frame, text="📁 Choose Photo", command=choose_image)
choose_img_button.pack(pady=5)

print_img_button = ttk.Button(frame, text="🖼️ Print Photo", command=lambda: print_image(img_path_var.get()))
print_img_button.pack(pady=5)

preview_label = ttk.Label(frame)
preview_label.pack(pady=10)


root.mainloop()

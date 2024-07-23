import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import socket
import ssl
import re
from urllib.parse import urlparse

def http_banner_grabbing(url, timeout=10):
    try:
        #Parse URL to get host, port and path
        parsed_url = urlparse(url)
        host = parsed_url.hostname
        port = parsed_url.port or 443  
        path = parsed_url.path or '/'  #if path is not specified
        
        #Create socket connection to web server
        with socket.create_connection((host, port), timeout=timeout) as s:
            #Wrap the socket with SSL/TLS
            context = ssl.create_default_context()
            with context.wrap_socket(s, server_hostname=host) as ss:
                #Send HTTP GET request
                ss.sendall(f"GET {path} HTTP/1.1\r\nHost: {host}\r\n\r\n".encode())
                #Receive the response
                response = ss.recv(4096).decode()
                #Check for redirection
                if response.startswith('HTTP/1.1 301') or response.startswith('HTTP/1.1 302'):
                    #Extract the new location from the response
                    location_header = re.search(r'Location: (.+)\r\n', response)
                    if location_header:
                        new_location = location_header.group(1)
                        #Recursive call to fetch response from the new location
                        return http_banner_grabbing(new_location, timeout)
                return response
    except socket.timeout:
        print("Connection timed out.")
    except socket.error as e:
        print(f"Socket error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    return None

def identify_web_server(response):
    #Check if the response is a redirection
    if response.startswith('HTTP/1.1 301') or response.startswith('HTTP/1.1 302'):
        return "Redirection"
    
    server_header_index = response.lower().find('server:')
    if server_header_index != -1:
        #Extract the server identifier from the response
        server_header_end_index = response.find('\r\n', server_header_index)
        server_header = response[server_header_index + len('server:'):server_header_end_index].strip()
        return server_header
    
    #If server not found above, analyze response body for some other common servers 
    if re.search(r"WordPress", response, re.IGNORECASE):
        return "WordPress"
    elif re.search(r"Joomla", response, re.IGNORECASE):
        return "Joomla"
    
    #If no server identification found
    return "Unknown"

def run_fingerprinting():
    url = url_entry.get()
    if not url:
        messagebox.showerror("Error", "Please enter a URL.")
        return
    
    response = http_banner_grabbing(url)
    if response:
        response_text.delete(1.0, tk.END)
        response_text.insert(tk.END, response)
        
        web_server = identify_web_server(response)
        server_label.config(text=f"Web Server: {web_server}")
    else:
        messagebox.showerror("Error", "Failed to retrieve response.")

def clear_results():
    url_entry.delete(0, tk.END)
    response_text.delete(1.0, tk.END)
    server_label.config(text="Web Server: ")

app = tk.Tk()
app.title("Web Server Fingerprinting Tool")
app.geometry("600x400")
url_label = ttk.Label(app, text="URL:")
url_entry = ttk.Entry(app, width=50)
run_button = ttk.Button(app, text="Run Fingerprinting", command=run_fingerprinting)
clear_button = ttk.Button(app, text="Clear Results", command=clear_results)
response_label = ttk.Label(app, text="Response:")
response_text = tk.Text(app, height=10, wrap=tk.WORD)
server_label = ttk.Label(app, text="Web Server: ")
url_label.pack(pady=5)
url_entry.pack(pady=5)
run_button.pack(pady=5)
clear_button.pack(pady=5)
server_label.pack(pady=5)
response_label.pack(pady=5)
response_text.pack(pady=5, fill=tk.BOTH, expand=True)
app.mainloop()
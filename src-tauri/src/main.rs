use std::{
    io::{Read, Write},
    net::{TcpListener, TcpStream},
    process::{Child, Command, Stdio},
    sync::Mutex,
    thread,
    time::{Duration, Instant},
};

use tauri::{Manager, RunEvent};

#[cfg(target_os = "windows")]
const SERVER_BINARY: &str = "mantooq-server.exe";
#[cfg(not(target_os = "windows"))]
const SERVER_BINARY: &str = "mantooq-server";

struct Server(Mutex<Option<Child>>);

fn start(app: tauri::AppHandle) -> std::io::Result<()> {
    let binary = app
        .path()
        .resource_dir()
        .map_err(std::io::Error::other)?
        .join("python/mantooq-server")
        .join(SERVER_BINARY);
    let data = app.path().app_data_dir().map_err(std::io::Error::other)?;
    std::fs::create_dir_all(&data)?;
    let listener = TcpListener::bind("127.0.0.1:0")?;
    let port = listener.local_addr()?.port();
    drop(listener);
    let child = Command::new(binary)
        .arg(format!("--server.port={port}"))
        .env("MANTOOQ_DATA_DIR", data)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()?;
    *app.state::<Server>().0.lock().unwrap() = Some(child);

    let deadline = Instant::now() + Duration::from_secs(45);
    while Instant::now() < deadline {
        if app.state::<Server>().0.lock().unwrap().as_mut().unwrap().try_wait()?.is_some() {
            break;
        }
        if let Ok(mut stream) = TcpStream::connect_timeout(
            &([127, 0, 0, 1], port).into(),
            Duration::from_millis(300),
        ) {
            stream.set_read_timeout(Some(Duration::from_millis(300)))?;
            stream.write_all(b"GET /_stcore/health HTTP/1.0\r\nHost: 127.0.0.1\r\n\r\n")?;
            let mut response = [0; 64];
            if stream.read(&mut response).is_ok_and(|n| response[..n].starts_with(b"HTTP/1.1 200") || response[..n].starts_with(b"HTTP/1.0 200")) {
                if let Some(window) = app.get_webview_window("main") {
                    let url = format!("http://127.0.0.1:{port}").parse().unwrap();
                    window.navigate(url).map_err(std::io::Error::other)?;
                }
                return Ok(());
            }
        }
        thread::sleep(Duration::from_millis(200));
    }
    Err(std::io::Error::other("Streamlit did not become ready"))
}

fn main() {
    tauri::Builder::default()
        .manage(Server(Mutex::new(None)))
        .setup(|app| {
            let handle = app.handle().clone();
            thread::spawn(move || {
                if start(handle.clone()).is_err() {
                    if let Some(mut child) = handle.state::<Server>().0.lock().unwrap().take() {
                        let _ = child.kill();
                        let _ = child.wait();
                    }
                    if let Some(window) = handle.get_webview_window("main") {
                        let _ = window.eval("startupError()");
                    }
                }
            });
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("failed to build منطوق")
        .run(|app, event| {
            if let RunEvent::Exit = event {
                if let Some(mut child) = app.state::<Server>().0.lock().unwrap().take() {
                    let _ = child.kill();
                    let _ = child.wait();
                }
            }
        });
}

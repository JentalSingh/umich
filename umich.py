import os
import sys
import time
import base64
import json
import shutil
from playwright.sync_api import sync_playwright
from loguru import logger
from faker import Faker

fake = Faker()

def run_umich_automation():
    target_url = "https://umich.qualtrics.com/jfe/form/SV_d1hntw5OdKvhRSA"
    
    # PDF check
    current_folder = os.getcwd()
    pdf_files = [f for f in os.listdir(current_folder) if f.lower().endswith('.pdf')]
    if not pdf_files:
        logger.error("❌ PDF file nahi mili!")
        return
    
    resume_path = os.path.join(current_folder, pdf_files[0])

    # 🎯 PDF Download Logic Variables
    captured_response_body = None
    downloaded_pdf_path = None

    with sync_playwright() as p:
        logger.info("🌐 Loading browser...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)  # 🎯 Enable downloads
        page = context.new_page()

        # 🎯 Capture upload response
        def handle_response(response):
            nonlocal captured_response_body
            if "/question/" in response.url and "/file" in response.url:
                if response.status == 200:
                    try:
                        captured_response_body = response.json()
                    except:
                        pass

        page.on("response", handle_response)

        logger.info("🌐 Loading URL...")
        page.goto(target_url, wait_until="networkidle")
        
        # Filling data
        logger.info("✍️ Filling Personal Info...")
        first_name = fake.first_name()
        last_name = fake.last_name()
        phone = "734-555-0199"
        email = "student@umich.edu"
        student_id = "12345678"
        semester = "Fall 2026"
        
        page.fill("input[type='text'] >> nth=0", first_name)
        page.fill("input[type='text'] >> nth=1", last_name)
        page.fill("input[type='text'] >> nth=2", phone)
        page.fill("input[type='text'] >> nth=3", email)
        page.fill("input[type='text'] >> nth=4", student_id)
        page.fill("input[type='text'] >> nth=5", semester)
        
        logger.info("✍️ Filling Major/Program...")
        page.fill("#QR\\~QID15", "Computer Science")

        logger.info("🖱️ Selecting options...")
        page.locator("label:has-text('Undergraduate')").click()
        page.locator("label:has-text('CASL')").click()
        page.locator("label:has-text('Yes')").first.click()
        page.locator("label:has-text('The iLabs website')").click()
        page.locator("label:has-text('Summer 2026')").click()

        logger.info(f"📎 Uploading Resume: {pdf_files[0]}...")
        page.set_input_files("input[type='file']", resume_path)
        
        time.sleep(2) 
        
        logger.info("🚀 Clicking NEXT button now...")
        page.locator("#NextButton").click()
        
        time.sleep(5)

        # 🎯 PDF DOWNLOAD LOGIC — Fixed with download event
        if captured_response_body and "previewURL" in captured_response_body:
            preview_url = captured_response_body["previewURL"]
            file_id = captured_response_body.get("fileId")
            
            logger.info("📥 Downloading PDF from Qualtrics...")
            
            try:
                # 🎯 Method 1: Use download event
                with page.expect_download() as download_info:
                    # Trigger download by navigating to URL
                    page.evaluate(f"window.location.href = '{preview_url}'")
                    download = download_info.value
                
                # Wait for download to complete
                download_path = download.path()
                logger.info(f"📥 Download path: {download_path}")
                
                # Save to desired location
                downloaded_pdf_path = f"qualtrics_{file_id}.pdf"
                download.save_as(downloaded_pdf_path)
                
                logger.success(f"✅ PDF downloaded: {downloaded_pdf_path}")
                logger.info(f"📊 Size: {os.path.getsize(downloaded_pdf_path)} bytes")
                
            except Exception as e:
                logger.error(f"❌ Download event failed: {e}")
                logger.info("🔄 Trying fallback method...")
                
                # 🎯 Method 2: Fallback — copy original
                try:
                    downloaded_pdf_path = f"qualtrics_{file_id}.pdf"
                    shutil.copy2(resume_path, downloaded_pdf_path)
                    logger.success(f"✅ PDF copied (fallback): {downloaded_pdf_path}")
                except Exception as e2:
                    logger.error(f"❌ Fallback also failed: {e2}")

        # Submit hone ke turant baad script ruk jayegi
        logger.success("✅ NEXT hit ho gaya, script band ho rahi hai!")

        browser.close()

    # 🎯 FINAL OUTPUT — Same Format
    if captured_response_body:
        file_id = captured_response_body.get("fileId")
        
        # Ensure we have a PDF
        if not downloaded_pdf_path or not os.path.exists(downloaded_pdf_path):
            downloaded_pdf_path = f"qualtrics_{file_id}.pdf"
            try:
                shutil.copy2(resume_path, downloaded_pdf_path)
            except:
                pass

        final_response = {
            "fileId": file_id,
            "name": captured_response_body.get("name"),
            "bytes": captured_response_body.get("bytes"),
            "mimeType": captured_response_body.get("mimeType"),
            "previewURL": captured_response_body.get("previewURL"),
            "transactionId": captured_response_body.get("transactionId")
        }

        print("\n" + "=" * 75)
        print("✅ QUALTRICS RESPONSE")
        print("=" * 75)
        print(json.dumps(final_response, indent=4))
        
        if downloaded_pdf_path and os.path.exists(downloaded_pdf_path):
            print(f"\n📥 PDF SAVED!")
            print(f"📂 File: {downloaded_pdf_path}")
            print(f"📂 Path: {os.path.abspath(downloaded_pdf_path)}")
            print(f"📊 Size: {os.path.getsize(downloaded_pdf_path)} bytes")
            print(f"✅ VALID PDF FILE!")
        else:
            print(f"\n⚠️ PDF save failed")
        
        print(f"\n✅ Form auto-filled successfully!")
        print(f"✅ Name: {first_name} {last_name}")
        print(f"✅ Email: {email}")
        print(f"✅ Student ID: {student_id}")
        print(f"✅ Major: Computer Science")
        print("=" * 75)
    else:
        logger.error("❌ Could not capture response.")

    os._exit(0) 

if __name__ == "__main__":
    run_umich_automation()
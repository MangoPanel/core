from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import tempfile
from pathlib import Path
import shutil
import logging
from graph import app as langgraph_app
from documents import Manga

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

#CORS for node.js frontend (idk if needed)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://localhost:3001"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024 

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH


def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok'}), 200


@app.route('/api/process-pdf', methods=['POST'])
def process_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only PDF files are allowed'}), 400
    
    steps = request.args.get('steps', 'ocr,translate').split(',')
    
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp(prefix='manga_processing_')
        logger.info(f"Created temp directory: {temp_dir}")
        
        input_dir = Path(temp_dir) / 'input'
        output_dir = Path(temp_dir) / 'output'
        input_dir.mkdir()
        output_dir.mkdir()
        
        pdf_path = input_dir / secure_filename(file.filename)
        file.save(str(pdf_path))
        logger.info(f"Saved PDF to: {pdf_path}")
        
        work_dir = Path(temp_dir) / 'work'
        work_dir.mkdir()
        logger.info(f"Created work directory: {work_dir}")
        
        logger.info("Creating Manga object...")
        manga = Manga(input_dir, work_dir=work_dir / 'manga_pages')
        logger.info(f"Manga object created with {len(manga._pages)} pages")
        
        # Invoke the LangGraph workflow
        logger.info("Starting LangGraph workflow (OCR -> Translation -> PDF generation)...")
        result = langgraph_app.invoke({
            "oryginal_manga": manga,
            "inpainted_manga": None,
            "translated_manga": None,
            "oryginal_json_representation": None,
            "translated_json_representation": None,
            "work_dir": work_dir,
            "output_pdf_path": None,
        })
        logger.info("LangGraph workflow completed")
        
        processed_pdf_path = Path(result["output_pdf_path"])
        logger.info(f"Processed PDF path: {processed_pdf_path}")
        
        if not processed_pdf_path.exists():
            raise FileNotFoundError("Processed PDF not found")
        
        response = send_file(
            str(processed_pdf_path),
            mimetype='application/pdf',
            as_attachment=True,
            download_name='translated_' + secure_filename(file.filename)
        )
        
        @response.call_on_close
        def cleanup():
            try:
                if temp_dir and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Error cleaning up temporary directory: {e}")
        
        return response
    
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return jsonify({'error': f'Failed to process PDF: {str(e)}'}), 500


@app.route('/api/status/<job_id>', methods=['GET'])
def get_status(job_id):
    # TODO: Implement job status tracking
    return jsonify({'status': 'processing', 'progress': 50}), 200


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)

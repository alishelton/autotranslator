from google.cloud import vision_v1p3beta1 as vision
from google.cloud import translate
from google.cloud import storage
import os
import json
import io

# OS credentials path setup
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/alishelton/Desktop/autotranslations/backend/credentials.json"

# Constants
FILE_PATH = "/Users/alishelton/Desktop/autotranslations/test_scans/multi-page-test_1.pdf"
FILE_URI = "gs://mangatranslator/multi-page-test_1.pdf"
BUCKET_URI = "gs://mangatranslations/"
TARGET_LANGUAGE = "en"
MIN_CONFIDENCE = 0.80

"""
Steps

1. upload file to gcs from frontend -- Backend assumes this is complete 
2. trigger function on file upload (check file type if image, use batch client, if pdf, use async client) - DETECT TEXT
3. Wait for all results in new bucket
4. Trigger function on bucket uploads -- Translate and edit image
5. Once finished, return new file to the frontend

"""

# Text detection and translation

############################################################
# LAMBDA 1 - Detect text and place in new bucket
############################################################

def process_new_manga(event, context):
	source_bucket, name, content_type = event['bucket'], event['name'], event['contentType']
	file_uri = 'gs://' + source_bucket + '/' + name
	destination_bucket_uri = 'gs://mangatranslations/' + name + '-'
	async_text_detection(file_uri, destination_bucket_uri, content_type)

"""
Detects text in a pdf file and output text findings to a cloud storage
bucket

"""
def async_text_detection(file_uri, bucket_uri, content_type):
	vision_client = vision.ImageAnnotatorClient()

	# Up to batch_size pages in a result output
	batch_size = 70
	feature = vision.types.Feature(
		type=vision.enums.Feature.Type.DOCUMENT_TEXT_DETECTION)

	gcs_source = vision.types.GcsSource(uri=file_uri)
	input_config = vision.types.InputConfig(
		gcs_source=gcs_source, mime_type=content_type)

	gcs_destination = vision.types.GcsDestination(uri=bucket_uri)
	output_config = vision.types.OutputConfig(
		gcs_destination=gcs_destination, batch_size=batch_size)

	async_request = vision.types.AsyncAnnotateFileRequest(
		features=[feature], input_config=input_config,
		output_config=output_config)

	response = vision_client.async_batch_annotate_files(
		requests=[async_request])


#################################################################
# LAMBDA 2 - Translate text, fix onto image, put in final bucket
#################################################################

def translate_and_write(event, context):
	source_file_bucket, json_output_name = event['bucket'], event['name']
	source_file_name = json_output_name.split('/')[0]



def retrieve_from_storage(bucket_name, file_name):
	storage_client = storage.Client()
	bucket = storage_client.get_bucket(bucket_name=bucket_name)



"""
Translates the input paragraphs from the src to the target language, returns a list containing:

(translation, bounding_box)

"""
def translate_text(paragraphs, src_lang, target_lang):
	translate_client = translate.Client()
	print('Translating text from {} into {}'.format(src_lang, target_lang))

	translations = []
	for p_counter, paragraph in enumerate(paragraphs):
		print('PARAGRAPH {}'.format(p_counter))
		translated_text = translate_client.translate(paragraph[0], target_language=target_lang, source_language=src_lang)
		print('Translation: {} \nBounding Box: {}\nCondfidence: {}'.format(translated_text, paragraph[1], paragraph[2]))
		translations.append((translated_text['translatedText'], paragraph[1]))
	return translations

async_text_detection(FILE_URI, BUCKET_URI, 'application/pdf')

######################################
######################################
######### Image manipulation #########
######################################
######################################

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

FONT_PATH = "/Users/alishelton/Desktop/autotranslations/backend/open-sans/OpenSans-Bold.ttf"
INCREASE_BOUNDARY_PIXELS = 10

"""
Picks forms multiple lines of of plaintext based on a max allowed width, 
returns a list of the lines

"""
def text_wrap(text, font, max_width):
    lines = []
    # If the width of the text is smaller than image width
    # we don't need to split it, just add it to the lines array
    # and return
    if font.getsize(text)[0] <= max_width:
        lines.append(text) 
    else:
        # split the line by spaces to get words
        words = text.split(' ')  
        i = 0
        # append every word to a line while its width is shorter than image width
        while i < len(words):
            line = ''         
            while i < len(words) and font.getsize(line + words[i])[0] <= max_width:                
                line = line + words[i] + " "
                i += 1
            if not line:
                line = words[i]
                i += 1
            # when the line gets longer than the max width do not append the word, 
            # add the line to the lines array
            lines.append(line)    
    return lines

"""
Inserts the translated text

"""
def insert_translated_text(path, translations):
	im = Image.open(path)
	
	font = ImageFont.truetype(font=FONT_PATH, size=12)
	line_height = font.getsize('hg')[1]
	for translation, bounding_box in translations:
		left = bounding_box.vertices[0].x - INCREASE_BOUNDARY_PIXELS
		upper = bounding_box.vertices[0].y - INCREASE_BOUNDARY_PIXELS
		right = bounding_box.vertices[2].x + INCREASE_BOUNDARY_PIXELS
		lower = bounding_box.vertices[2].y + INCREASE_BOUNDARY_PIXELS
		box = (left, upper, right, lower)
	
		white_out = Image.new('RGBA', (right - left, lower - upper), 'white')
		im.paste(white_out, box)
		draw = ImageDraw.Draw(im)
		lines = text_wrap(translation, font, right - left)
		x, y = left, upper
		for line in lines:
			print('LINE: {}'.format(line))
			draw.text((x, y), line, fill='black', font=font)
			y += line_height

	im.show()

# insert_translated_text(FILE_PATH, translations)


# TESTING FUNCTIONS

"""
Detects text on a single page, returns a list of 3 tuples containing:

(paragraph, bounding_box, confidence)

"""
def detect_text_on_cloud(path):
	vision_client = vision.ImageAnnotatorClient()

	image = vision.types.Image()
	image.source.image_uri = path

	response = vision_client.document_text_detection(image=image)

	src_lang = ""
	paragraphs = []
	for page in response.full_text_annotation.pages:
		src_lang = page.property.detected_languages[0].language_code
		print('Source language: {}\n'.format(src_lang))
		for block in page.blocks:
			for paragraph in block.paragraphs:
				paragraph_text = ''.join([''.join([symbol.text for symbol in word.symbols]) for word in paragraph.words])
				if paragraph.confidence > MIN_CONFIDENCE:
					paragraphs.append((paragraph_text, paragraph.bounding_box, paragraph.confidence))

	return paragraphs, src_lang

"""
Detects text on a single page, returns a list of 3 tuples containing:

(paragraph, bounding_box, confidence)

"""
def detect_text_locally(path):
	vision_client = vision.ImageAnnotatorClient()

	with io.open(path, 'rb') as image_file:
		content = image_file.read()

	image = vision.types.Image(content=content)

	response = vision_client.document_text_detection(image=image)

	src_lang = ""
	paragraphs = []
	for page in response.full_text_annotation.pages:
		src_lang = page.property.detected_languages[0].language_code
		print('Source language: {}\n'.format(src_lang))
		for block in page.blocks:
			for paragraph in block.paragraphs:
				paragraph_text = ''.join([''.join([symbol.text for symbol in word.symbols]) for word in paragraph.words])
				if paragraph.confidence > MIN_CONFIDENCE:
					paragraphs.append((paragraph_text, paragraph.bounding_box, paragraph.confidence))

	return paragraphs, src_lang

# paragraphs, src_lang = detect_text_locally(FILE_PATH)
# translations = translate_text(paragraphs, src_lang, TARGET_LANGUAGE)





* Run the following commands
```bash
cd data-processor
mongoexport --ssl --host=cluster0-shard-00-00-oix69.mongodb.net --username="guess-what-mongo" --password="xxxxxxxxxx" --authenticationDatabase=xxxxxxxxxx --db=xxxxxxxxxx --collection=comments --type=csv --fields="id,message,reactions_all.summary.total_count,sad.summary.total_count,like.summary.total_count,love.summary.total_count,angry.summary.total_count,haha.summary.total_count,wow.summary.total_count,created_time,permalink_url,parent_post_id" --query="{message:{\$ne:\"\"}, message_tags:{\$exists:false}, parent_post_id:{\$not: /127434041553/}}" --out=comments_no_blank.csv
. env/bin/activate
pip install -r requirements.txt
python gen_label_and_pre_process.py
python gen_one_class_data.py
cd <path to tokenize>
python tokenize-csv.py 
rsync -rave "ssh -i <pem file>" <local_path>/*_tokenized.csv  ubuntu@<ip>:<path>

#AT SERVER
fasttext supervised -input complain_tokenized.csv -output complain -lr 1.0 -epoch 25 -wordNgrams 2
#fasttext test complain.bin complain_test_tokenized.csv
fasttext supervised -input question_tokenized.csv -output question -lr 1.0 -epoch 25 -wordNgrams 2
#fasttext test question.bin question_test_tokenized.csv
fasttext supervised -input negative_tokenized.csv -output negative -lr 1.0 -epoch 25 -wordNgrams 2
#fasttext test negative.bin negative_test_tokenized.csv
fasttext supervised -input positive_tokenized.csv -output positive -lr 1.0 -epoch 25 -wordNgrams 2
#fasttext test positive.bin positive_test_tokenized.csv 
```

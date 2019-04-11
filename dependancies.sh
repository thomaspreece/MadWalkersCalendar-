set -e 
read -r -p "This will install python dependancies. Continue? [y/N] " response
case $response in
    [yY][eE][sS]|[yY]) 
       read -r -p "Run pip as admin? [y/N] " response2
       case $response2 in
           [yY][eE][sS]|[yY]) 
               sudo pip install --upgrade google-api-python-client 
               sudo pip install lxml 
               sudo pip install requests
			   sudo pip install oauth2client
               ;;
           *)
               pip install --upgrade google-api-python-client 
               pip install lxml 
               pip install requests             
               pip install oauth2client			   
               ;;
	esac
	echo Successful!
        ;;
    *)
	echo Aborted
        ;;
esac


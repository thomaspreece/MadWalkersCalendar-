set -e
read -r -p "This will install ubuntu dependancies. Continue? [y/N] " response
case $response in
    [yY][eE][sS]|[yY])
    sudo apt-get update
    sudo apt-get install libxml2 libxml2-dev python-dev
	echo Ubuntu Pacakges Successful!
        ;;
    *)
	echo Ubuntu Packages Aborted
        ;;
esac

read -r -p "This will install python dependancies. Continue? [y/N] " response
case $response in
    [yY][eE][sS]|[yY])
       read -r -p "Run pip as admin? [y/N] " response2
       case $response2 in
           [yY][eE][sS]|[yY])
               sudo pip install --upgrade google-api-python-client
               sudo pip install lxml
               sudo pip install requests
               ;;
           *)
               pip install --upgrade google-api-python-client
               pip install lxml
               pip install requests
               ;;
	esac
	echo Python Packages Successful!
        ;;
    *)
	echo Python Packages Aborted
        ;;
esac

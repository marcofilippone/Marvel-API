# Marvel-API
This assignment is divided into two parts. The first part requires you to write the code to connect to the Marvel Developer Portal and retrieve the data specified below. The second part requires that you write the code to create an API to store the data you retrieve and allow users to interact with them. 


## Part  1

Complete the required steps to gain access to Marvel developer Portal. Once you do, write the code to complete the following tasks:

1. Provide a list of 30 Marvel characters
2. Retrieve the Ids for all the characters in your list (in str form)
3. Retrieve the total number of Events available for all the characters in your list (in integer form)
4. Retrieve the total number of Series available for all the characters in your list  (in integer form)
5. Retrieve the total number of Comics available for all the characters in your list (in integer form)
6. Retrieve the Price of the most expensive comic that the character was featured in or all the characters in your list (in float form and USD)
7. Store the data above in a pandas DataFrame called df containing exactly in the following columns: Character Name, Character ID, Total Available Events, Total Available Series, Total Available Comics, Price of the Most Expensive Comic. If a character is not featured in Events, Series or Comics the corresponding entry should be filled in with a None (of NoneType). If a character does not have a Price the corresponding entry should be filled in with a None (of NoneType).
8. Save df to a file called data.csv


## Part 2

Once you are finished extracting the data above and saving it to a file, write the code to complete the following tasks:

1. Create an API that allows users to interact with the DataFrame generated in the Part 1 of the assignments.
2. Create a resource called Characters and route it to the url '/characters' and endpoint 'characters'.
3. Implement the following methods for this resource:
  a) Retrieve the whole DataFrame in json format; 
  b) Retrieve information for a single entry or for a list of entries identified by either the Character Name or the Character ID; 
  c) Add a new character to the existing DataFrame by specifying its characteristics (Character Name, Character ID, Available Events, Available Series, Available Comics, and Price of Comic). The API should restrict addition of characters with pre-existing Character IDs; 
  d) Add a new character to the existing DataFrame by specifying only the Character ID. The API should fill in the remaining information by extracting it from Marvel's API and appending to the DataFrame. The API should return an error if the provided character id is not found; 
  e) Delete a character or a list of characters by providing either the Character ID or the Character Name. The API should return an error if the character you are trying to delete does not exist in the DataFrame.
4. Protect both the addition and the deletion of characters using an OAuth authentication scheme whereby users can sign up and then log in to obtain an access token with limited scope and a duration of 1 hour.


Bonus

Write the code to enable users to modify the Price of the Most Expensive Comic by providing either the Character ID or the Character Name. The API should accept new prices in different currencies, including USD, EUR, GBP and CAD and transform them to the right values to the exanche rate of the considered date and time (+/- an hour).

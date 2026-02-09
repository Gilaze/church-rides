Check out the website here:
https://church-rides-gilaze7393-of35ddsq.leapcell.dev


My blog of this project:

The Application

Over winter break, I created and deployed an online transportation system for my church using python, SQL, Flask, and a service called Leapcell. 

A passenger, after creating a profile, can easily add himself/herself under a listed pickup location with a simple click of a button. The website displays the entire transportation list for that week updated real time and administrators can access a metric dashboard to help track attendance and send confirmation emails.

The Before

	The church offers a shuttle system, operating three vans, where poor freshmen without cars can sign up for a ride. Before, a freshman in need of a ride would have to fill out a long google form, inputting the same information every week. The deadline was Friday night, and if not met, then the passenger would have no choice but to take the bus (whose hours are not convenient).

	Every week someone would forget to fill out the google form. Many times, that person was me. There were multiple instances where a church friend texted me,

	“Bro, I forgot to fill the form.”
	“Form? Oh! Me, too.”
	
	If a person has no ride, then the likelihood of that person showing up to church decreases.

	I embarked on this project to prevent this from happening. 

Could I create a simple, efficient online transportation website that could ultimately increase church attendance?	


The System
The system consists of three main components:
Users
Rides
Automated Tasks 
Users
User Accounts
	I decided to implement user accounts because accounts store your personal information, meaning you only have to input your information once. This is useful because unlike a google form where you need to input your information each time, a function can pass the saved, mandatory information to drivers with a single click of a button.

	I created a login page using Flask-login and Werkzeug library where returning users can login using their username and password while new users can create an account in a new page. The Werkzeug library provides password encryption, and user credentials are safely stored in an online database. Users can also check the “Remember Me” button if they wish.

User Types
	The program includes three different user types: passenger, driver, and administrator.
	
	A passenger has only the basic privilege of adding himself/herself to a ride.

	A driver has the same privileges as a user, but also has the ability to create and remove pickup locations and assign himself/herself a passenger capacity. A driver can be a passenger, but a passenger cannot be a driver.

	Finally, an administrator has access to the administrator panel. The panel displays metrics for all rides for that week. It consists of a master list of all passengers, their pickup location, and their driver. An administrator can download the entire list as a pdf. Another box displays the emails of all passengers which can be copied all at once. 

If the church wants to email all passengers the confirmed ride list for that week, they would only need to copy and paste the already provided information they need. This makes the process prompt for both sides by eliminating the need to reinput information.

Rides
	You may have noticed that I use the term “pickup location” instead of “vehicle.” Initially, drivers were able to add their vehicles instead of pickup locations, and instead of driver capacity they would assign a vehicle capacity to their vehicle, not themselves.

	My church’s shuttle system consisted only of three vans. Each van would go to multiple freshman dormitories to pick up passengers. If a driver were to list their vehicle i.e. Ethan’s Van instead of listing a pickup location, this would cause confusion. 

Passengers are assigned a driver, and drivers rotate every week. How could passengers add themselves under an unknown driver? The pickup location system resolves this issue. By having the drivers create pickup locations, passengers don’t need to know who their driver is. 

Note that with this system, the same driver/vehicle would have to travel to multiple locations. Having a vehicle capacity won’t work because there isn’t one box for users to add themselves to one driver. Before, the system was designed so that students of different dorms would go to the same driver. Now, the driver is going to different dorms. This system led to probably the most important update of my website.

A driver capacity applies to the accumulated sum of passengers under all of a driver’s listed pickup locations.


Automated Tasks

	After completing the design of the system, I embarked on adding maintenance features to the website.

	First, I added a weekly ride reset feature using GitHub action. Every week at Monday 12am, GitHub action would run a script that removes all listed pickup locations and their listed passengers. The aim of this project is to remove as much manual work as possible, and by adding this feature, drivers don’t have to remember to remove their vehicle. However, if a driver wants to keep their vehicle (conversely not manually add their vehicle), then they can check the “Remember Vehicle” box under their profile to bypass this weekly reset.

	Second, I incorporated a health check system also using GitHub action. GitHub action runs the script every 15 minutes. The script sends a ping to the website, and if it receives a response, then nothing happens. If after 3 pings no response is received, then the script detects that the website is down. 



Finally, I added an automated email system triggered by the prior script when the website is down. An automated email is sent to the administrators alerting them of the outage along with an attached pdf of the most recent transportation list. Most times, when the website is down the cause is the code rather than the service, meaning that the database is still online which makes the automated email possible.

Relation to Fastopp

	Having worked with Fastopp before, some of the skills I gained from Fastopp proved useful when building this project. First, both projects used Object Relational Mapping (ORM). 

In the Fastopp store, the application allows you to manually add an item without having to hardcode it into the code. The application uses python to send a SQL query to the Leapcell to achieve this, and ORM serves as the necessary translator between the two subjects. Just like adding an item, the transportation website adds a pickup location in the same way.

Both applications also use object oriented programming. In the Fastopp store, there exists certain objects such as items which possess different attributes. The website equivalent would be user and pickup location classes which have different attributes such as driver capacity and user details.

Finally, both projects challenged my ability to scale the program. I learned that an online application requires many features such as a login, superuser, and more than just the purpose it serves.

Concluding Thoughts
	
	I really enjoyed building this project where I poured all my previous knowledge from class, Fastopp, and other projects to build something real. From enthusiastically thinking of what features to add to seeing actual users on my website, I had the privilege of pursuing my passion for software engineering while being able to make a meaningful impact on a community. 



	
	
	

	

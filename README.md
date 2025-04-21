## Odisha Online Voting System

# Overview

This is an online voting system project designed to facilitate elections in Odisha, India. The system allows voters to register, log in, cast votes, and view results, while providing an admin dashboard for managing candidates and election data. Built using Flask, SQLite, and Bootstrap, this project aims to provide a secure and user-friendly voting experience.

# Features

Voter registration and login with district-based selection.
Candidate registration and management by admin.
Voting system with district-wise candidate selection.
Real-time election results display with charts.
Admin dashboard to monitor vote trends.

# Prerequisites





Python 3.x



Flask



SQLite



Bootstrap (via CDN)



Basic knowledge of HTML, CSS, and JavaScript

Installation





Clone the repository:

git clone https://github.com/your-username/odisha-online-voting-system.git



Navigate to the project directory:

cd odisha-online-voting-system



Install required packages:

pip install flask flask-wtf bcrypt



Run the application:

python app.py



Open your browser and go to http://localhost:5000.

Usage





Register as Voter: Visit /register, select your district from the dropdown, and set a password.



Login: Use /login to access the voting page.



Vote: Choose a candidate from your district on the /vote page.



View Results: Check election results on /results.



Admin Access: Log in as admin on /admin_login to manage candidates via /admin_add_candidate.

Database





The project uses a SQLite database (voting.db) with tables for voters, candidates, and votes.



To reset the database, use the /reset_database route (admin access required).

Contributing

Feel free to fork this repository, make improvements, and submit pull requests. Suggestions for new features or bug fixes are welcome!

License

This project is open-source under the MIT License.

Contact

For questions or support, reach out to the developer at your-email@example.com.

Acknowledgements





Inspired by the need for a digital voting solution in Odisha.



Built with guidance from online resources and community support.

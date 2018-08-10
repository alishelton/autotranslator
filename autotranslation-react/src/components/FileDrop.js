import React, { Component } from 'react';
import Dropzone from 'react-dropzone';
import '../filedrop.css';

class FileDrop extends Component {
	constructor(props) {
		super(props)
		this.state = { files: [] }
	}

	onDrop(files) {
		this.setState({
			files
		});
	}

	render() {
		return (
			<div>
				<div>
		    		<Dropzone onDrop={this.onDrop.bind(this)}>
		        		
		      		</Dropzone>
		    	</div>
		    	<aside>
		      		<h2>Dropped files</h2>
		      		<ul>
		        	{
		          		this.state.files.map(f => <li key={f.name}>{f.name} - {f.size} bytes</li>)
		        	}
		      		</ul>
		    	</aside>
	    	</div>
		);
	}
}

export default FileDrop;
import React, { Component } from 'react';
import { Container, Row, Col, Button } from 'reactstrap';
import logo from './logo.svg';
import FileDrop from './components/FileDrop';
import Title from './components/Title';
import './App.css';

class App extends Component {
  render() {
    return (
      <Container className="App">
        <h1>Manga Auto Translator</h1> 
        <Col>
          <FileDrop />  
        </Col>
      </Container>
    );
  }
}

export default App;
